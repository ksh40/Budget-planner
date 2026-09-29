from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, EventUpdate
from .forms import EventForm, EventUpdateForm
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from .forms import EventForm, EventUpdateForm, EvidenceForm


def event_list_view(request):
    events = Event.objects.filter(status='approved').order_by('-date')
    return render(request, 'events/event_list.html', {'events': events})


def event_detail_view(request, pk):
    from django.db.models import Q
    from analytics.models import EventView

    event = get_object_or_404(
        Event,
        Q(status='approved') | Q(organiser=request.user) if request.user.is_authenticated else Q(status='approved'),
        pk=pk
    )

    # Record a view
    EventView.objects.create(event=event)

    updates = event.updates.order_by('-created_at')
    return render(request, 'events/event_detail.html', {'event': event, 'updates': updates})


@login_required
@login_required
def event_create_view(request):
    if request.user.role != 'organiser':
        messages.error(request, 'Only organisers can create events.')
        return redirect('event_list')

    if not request.user.is_verified:
        messages.error(request, 'You must be verified before creating events.')
        return redirect('verification_status')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organiser = request.user

            # Blockchain permit verification
            permit_number = form.cleaned_data.get('permit_number')
            issuing_authority = form.cleaned_data.get('issuing_authority')

            if permit_number and issuing_authority:
                try:
                    from blockchain.blockchain import verify_permit
                    result = verify_permit(permit_number, issuing_authority)
                    event.permit_verified = result['is_valid']
                    event.permit_tx_hash = result['tx_hash']
                    event.permit_block_number = result['block_number']
                    if not result['is_valid']:
                        messages.warning(request, f'Permit could not be verified on the blockchain. Transaction recorded: {result["tx_hash"]}. Your event has been submitted but admin will review the permit manually.')
                    else:
                        messages.success(request, f'Permit verified on blockchain. Transaction: {result["tx_hash"]}')
                except Exception as e:
                    messages.warning(request, 'Blockchain verification temporarily unavailable. Event submitted for manual review.')

            event.save()
            from accounts.emails import send_event_submitted_admin_email
            send_event_submitted_admin_email(event)
            messages.success(request, 'Event submitted for admin review.')
            return redirect('organiser_dashboard')
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form, 'action': 'Create'})


@login_required
def event_edit_view(request, pk):
    event = get_object_or_404(Event, pk=pk, organiser=request.user)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Event updated and resubmitted for review.')
            return redirect('organiser_dashboard')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {'form': form, 'action': 'Edit'})


@login_required
def event_delete_view(request, pk):
    event = get_object_or_404(Event, pk=pk, organiser=request.user)

    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted.')
        return redirect('organiser_dashboard')

    return render(request, 'events/event_confirm_delete.html', {'event': event})


@login_required
def event_update_post_view(request, pk):
    event = get_object_or_404(Event, pk=pk, organiser=request.user)

    if request.method == 'POST':
        form = EventUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.event = event
            update.save()
            messages.success(request, 'Update posted.')
            return redirect('event_detail', pk=pk)
    else:
        form = EventUpdateForm()

    return render(request, 'events/event_update_form.html', {'form': form, 'event': event})


@login_required
def organiser_dashboard_view(request):
    if request.user.role != 'organiser':
        return redirect('event_list')

    events = Event.objects.filter(organiser=request.user).order_by('-created_at')
    return render(request, 'events/organiser_dashboard.html', {'events': events})


@staff_member_required
def start_review(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.status == 'pending':
        event.status = 'under_review'
        event.review_started_at = timezone.now()
        event.save()
        messages.success(request, 'Event moved to review.')
    return redirect('event_admin_detail', pk=pk)


@staff_member_required
def add_evidence(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.event = event
            evidence.admin = request.user
            if request.FILES.get('document'):
                from accounts.utils import hash_document
                evidence.document_hash = hash_document(
                    request.FILES['document']
                )
            evidence.save()
            messages.success(request, 'Evidence recorded.')
            return redirect('event_admin_detail', pk=pk)
    else:
        form = EvidenceForm()
    return render(request, 'events/add_evidence.html', {'form': form, 'event': event})

@staff_member_required
def decide_event(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.status != 'under_review':
        messages.error(request, 'Event must be under review before a decision can be made.')
        return redirect('event_admin_detail', pk=pk)
    if not event.evidence.exists():
        messages.error(request, 'At least one piece of evidence is required before deciding.')
        return redirect('event_admin_detail', pk=pk)
    if request.method == 'POST':
        decision = request.POST.get('decision')
        if decision == 'approve':
            event.status = 'approved'
            event.save()
            from accounts.emails import send_event_approved_email
            send_event_approved_email(event)
        elif decision == 'reject':
            event.status = 'rejected'
            event.save()
            from accounts.emails import send_event_rejected_email
            send_event_rejected_email(event)
        messages.success(request, f'Event has been {event.status}.')
    return redirect('event_admin_detail', pk=pk)

@staff_member_required
def event_admin_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form = EvidenceForm()
    return render(request, 'events/event_admin_detail.html', {'event': event, 'form': form})

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .models import Event


@staff_member_required
def pending_events(request):
    pending = Event.objects.filter(status='pending').order_by('date')

    return render(
        request,
        'events/pending_events.html',
        {'pending_events': pending}
    )