from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.models import Location, Subscription, LocationTag, User
from core.forms import LocationForm


@login_required
def locations(request):
    user = request.user
    form = LocationForm()
    if not user.stripe_id:
        user.create_stripe_customer()
    if request.method == "POST":
        # Check if the user used the drop down or entered a code (drop down is priority)
        if len(request.POST.get('location_code')) == 0:
            form = LocationForm(request.POST)
            if form.is_valid():
                form_location = form.cleaned_data['location']
                location = get_object_or_404(Location, name=form_location)
                location_code = location.code
        else:
            location_code = request.POST.get('location_code').upper()
        try:
            location = Location.objects.get(code=location_code)
            return redirect(location.get_absolute_url())
        except Location.DoesNotExist:
            if location_code:
                messages.error(request, "There is no location that matches that code.")
            else:
                messages.error(request, "Please enter a code.")

    return render(request, "core/locations.djhtml", {
        "form": form
    })


@login_required
def location(request, location_code):
    boxesCheckedIn = 0
    communityBoxesCheckedIn = 0
    user = request.user
    location = get_object_or_404(Location, code=location_code.upper())
    complete = False

    if request.method == "POST":
        subscription_id = request.POST.get('subscription_id')
        for sub in user.get_subscriptions():
            boxesCheckedIn = boxesCheckedIn + int((LocationTag.objects.filter(subscription_id=sub.id)).count()/2)
        communityBoxesCheckedIn = int((LocationTag.objects.all()).count()/2) + 100
        try:
            subscription = user.subscriptions.active().get(pk=subscription_id)
        except Subscription.DoesNotExist as ex:
            # TODO: handle this
            raise ex

        box_plural = lambda n: pluralize(n, "box,boxes")

        with transaction.atomic():
            if len(request.POST.get('number_of_boxes')) > 0 and int(request.POST.get('number_of_boxes')) > 0:
                number_of_boxes = int(request.POST.get('number_of_boxes', 1))
                if subscription.can_tag_location(location, number_of_boxes):
                    subscription.tag_location(location, number_of_boxes)
                    if location.service == location.CHECKIN:
                        msg = "You have returned {} {}.".format(
                            number_of_boxes, box_plural(number_of_boxes)
                        )
                    else:
                        msg = "You have checked out {} {}.".format(
                            number_of_boxes, box_plural(number_of_boxes)
                        )
                    complete = True
                    messages.success(request, msg)
                else:
                    if location.service == location.CHECKIN:
                        if number_of_boxes == 1:
                            msg = "You have returned all of your boxes for this subscription."
                        else:
                            msg = ("You do not have {} {} checked out with this "
                                "subscription.").format(
                                    number_of_boxes, box_plural(number_of_boxes)
                                )
                    else:
                        if number_of_boxes == 1:
                            msg = (
                                "You do not have enough boxes to check out with "
                                "this subscription."
                            )
                        else:
                            msg = (
                                "You do not have enough boxes to check out {} {} "
                                "with this subscription."
                            ).format(number_of_boxes, box_plural(number_of_boxes))

                    messages.error(request, msg)
            else:
                msg = (
                    "Please enter a valid positive number"
                )
                messages.error(request, msg)

    subscriptions = [
        {
            "id": subscription.pk,
            "name": subscription.plan_display,
            "max_boxes": subscription.number_of_boxes,
            "available_boxes": subscription.available_boxes,
        } for subscription in user.subscriptions.active()
    ]

    return render(
        request, "core/location.djhtml", {
            "location": location,
            "subscriptions": subscriptions,
            "boxesCheckedIn": boxesCheckedIn,
            "communityBoxesCheckedIn": communityBoxesCheckedIn,
            "complete": complete,
        }
    )
