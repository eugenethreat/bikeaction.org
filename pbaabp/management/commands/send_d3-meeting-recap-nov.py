from django.core.management.base import BaseCommand

from events.models import EventRSVP, EventSignIn, ScheduledEvent
from pbaabp.email import send_email_message

SENT = []


class Command(BaseCommand):
    help = "Send D3 meeting recap to anyone who RSVP'd or signed in to the November District 3 monthly meeting"

    def handle(self, *args, **options):
        # Get the event by slug
        try:
            event = ScheduledEvent.objects.get(slug="pba-district-3-monthly-meeting")
        except ScheduledEvent.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Event with slug "pba-district-3-monthly-meeting" not found')
            )
            return

        self.stdout.write(f"Found event: {event.title}")

        # Get all sign-ins for this event
        sign_ins = EventSignIn.objects.filter(event=event)
        self.stdout.write(f"Found {sign_ins.count()} sign-ins")

        # Get all RSVPs for this event
        rsvps = EventRSVP.objects.filter(event=event).select_related("user")
        self.stdout.write(f"Found {rsvps.count()} RSVPs")

        # Send email to each person who signed in
        for sign_in in sign_ins:
            if sign_in.email.lower() not in SENT:
                send_email_message(
                    "d3-meeting-recap-nov",
                    "Philly Bike Action <noreply@bikeaction.org>",
                    [sign_in.email],
                    {
                        "first_name": sign_in.first_name,
                        "last_name": sign_in.last_name,
                    },
                    reply_to=["district3@bikeaction.org"],
                )
                SENT.append(sign_in.email.lower())
                self.stdout.write(f"Sent to {sign_in.email} (sign-in)")
            else:
                self.stdout.write(f"Skipping duplicate: {sign_in.email}")

        # Send email to each person who RSVP'd
        for rsvp in rsvps:
            # Get email and name from user object if available, otherwise from RSVP fields
            if rsvp.user:
                email = rsvp.user.email
                first_name = rsvp.user.first_name or rsvp.first_name or ""
                last_name = rsvp.user.last_name or rsvp.last_name or ""
            else:
                email = rsvp.email
                first_name = rsvp.first_name or ""
                last_name = rsvp.last_name or ""

            if email and email.lower() not in SENT:
                send_email_message(
                    "d3-meeting-recap-nov",
                    "Philly Bike Action <noreply@bikeaction.org>",
                    [email],
                    {
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                    reply_to=["district3@bikeaction.org"],
                )
                SENT.append(email.lower())
                self.stdout.write(f"Sent to {email} (RSVP)")
            elif email:
                self.stdout.write(f"Skipping duplicate: {email}")

        self.stdout.write(self.style.SUCCESS(f"Sent {len(SENT)} emails total"))
