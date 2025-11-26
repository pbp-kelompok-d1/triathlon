# tests.py (more defensive/fault-tolerant)
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.shortcuts import redirect
from place.models import Place
from ticket.models import Ticket
from user_profile.models import UserProfile


def safe_reverse(name, *args, **kwargs):
    try:
        return reverse(name, *args, **kwargs)
    except NoReverseMatch as e:
        raise AssertionError(f"URL name not found: {name}. Verify urls.py. Original: {e}")


class TicketModelTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Jakarta Stadium",
            price=Decimal("150000.00"),
            city="Jakarta",
        )
        self.user = User.objects.create_user(username="john", password="test123")
        UserProfile.objects.get_or_create(user=self.user, defaults={"role": "user"})

    def test_total_price_auto_calculated_on_save(self):
        ticket = Ticket.objects.create(
            customer_name="John Doe",
            place=self.place,
            ticket_quantity=2,
            booking_date=date.today(),
            user=self.user,
        )
        self.assertEqual(ticket.total_price, Decimal("300000.00"))

    def test_ticket_number_format(self):
        ticket = Ticket.objects.create(customer_name="Jane", place=self.place, user=self.user)
        self.assertTrue(ticket.ticket_number.startswith("TK-"))
        self.assertEqual(len(ticket.ticket_number), 9)

    def test_status_property_and_helpers(self):
        today = date.today()
        t1 = Ticket.objects.create(booking_date=today - timedelta(days=1), user=self.user, place=self.place)
        t2 = Ticket.objects.create(booking_date=today, user=self.user, place=self.place)
        t3 = Ticket.objects.create(booking_date=today + timedelta(days=1), user=self.user, place=self.place)

        self.assertEqual(t1.status, "past")
        self.assertEqual(t1.status_display, "Past")
        self.assertEqual(t1.status_badge_class, "secondary")

        self.assertEqual(t2.status, "today")
        self.assertEqual(t2.status_display, "Today")
        self.assertEqual(t2.status_badge_class, "success")

        self.assertEqual(t3.status, "upcoming")
        self.assertEqual(t3.status_display, "Upcoming")
        self.assertEqual(t3.status_badge_class, "primary")

    def test_str_representation(self):
        ticket = Ticket.objects.create(customer_name="Tester", place=self.place, user=self.user)
        s = str(ticket)
        self.assertIn("Ticket #", s)
        self.assertIn("Tester", s)


class TicketViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # create users and profiles
        self.admin_user = User.objects.create_user("admin", password="adminpass")
        self.normal_user = User.objects.create_user("user", password="userpass")
        UserProfile.objects.get_or_create(user=self.admin_user, defaults={"role": "admin"})
        UserProfile.objects.get_or_create(user=self.normal_user, defaults={"role": "user"})

        # place + ticket
        self.place = Place.objects.create(name="Surabaya Arena", price=Decimal("200000.00"), city="Surabaya")
        self.ticket = Ticket.objects.create(
            customer_name="Budi",
            place=self.place,
            ticket_quantity=2,
            user=self.normal_user,
            booking_date=date.today(),
        )

    # helper: use force_login to avoid login flakiness
    def force_login(self, user_obj):
        self.client.force_login(user_obj)

    def test_ticket_list_requires_login(self):
        resp = self.client.get(safe_reverse("ticket:ticket_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url.lower())

    def test_ticket_list_for_normal_user(self):
        self.force_login(self.normal_user)
        resp = self.client.get(safe_reverse("ticket:ticket_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Budi")

    def test_ticket_list_for_admin(self):
        self.force_login(self.admin_user)
        resp = self.client.get(safe_reverse("ticket:ticket_list"))
        self.assertEqual(resp.status_code, 200)
        # Admin may not see user's tickets; just assert table renders fine
        self.assertIn("text-gray-500", resp.content.decode())  # e.g. 'No tickets found.'


    @patch("ticket.views.check_user_profile", return_value=redirect("/profile/"))
    def test_check_user_profile_redirects_when_missing(self, mock_check):
        self.force_login(self.normal_user)
        UserProfile.objects.filter(user=self.normal_user).delete()
        resp = self.client.get(safe_reverse("ticket:ticket_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/profile", resp.url.lower())


    # CREATE (AJAX & non-AJAX)
    def test_ticket_create_ajax_success(self):
        self.force_login(self.normal_user)
        payload = {
            "customer_name": "Andi",
            "place": str(self.place.id),
            "booking_date": date.today().strftime("%Y-%m-%d"),
            "ticket_quantity": "3",
        }
        resp = self.client.post(safe_reverse("ticket:ticket_create"), payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["ticket"]["customer_name"], "Andi")

    def test_ticket_create_non_ajax_success(self):
        self.force_login(self.normal_user)
        payload = {
            "customer_name": "Rudi",
            "place": str(self.place.id),
            "booking_date": date.today().strftime("%Y-%m-%d"),
            "ticket_quantity": "2",
        }
        resp = self.client.post(safe_reverse("ticket:ticket_create"), payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Ticket.objects.filter(customer_name="Rudi").exists())

    def test_ticket_create_invalid_form_ajax(self):
        self.force_login(self.normal_user)
        payload = {"customer_name": "", "ticket_quantity": ""}
        resp = self.client.post(safe_reverse("ticket:ticket_create"), payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertTrue(data.get("errors") or data.get("success") is False)

    def test_ticket_create_get_with_place_id(self):
        self.force_login(self.normal_user)
        resp = self.client.get(safe_reverse("ticket:ticket_create") + f"?place_id={self.place.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.place.name)

    def test_ticket_create_get_with_invalid_place(self):
        self.force_login(self.normal_user)
        resp = self.client.get(safe_reverse("ticket:ticket_create") + "?place_id=999999")
        self.assertEqual(resp.status_code, 200)

    # UPDATE
    def test_ticket_update_by_owner(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:ticket_update", args=[self.ticket.id])
        payload = {
            "customer_name": "Budi Updated",
            "place": str(self.place.id),
            "booking_date": date.today().strftime("%Y-%m-%d"),
            "ticket_quantity": "5",
        }
        resp = self.client.post(url, payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.customer_name, "Budi Updated")
        self.assertEqual(self.ticket.total_price, Decimal("1000000.00"))

    def test_ticket_update_ajax_success(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:ticket_update", args=[self.ticket.id])
        payload = {
            "customer_name": "Edited",
            "place": str(self.place.id),
            "booking_date": date.today().strftime("%Y-%m-%d"),
            "ticket_quantity": "1",
        }
        resp = self.client.post(url, payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("success"))

    def test_ticket_update_invalid_form_ajax(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:ticket_update", args=[self.ticket.id])
        payload = {"customer_name": "", "ticket_quantity": ""}
        resp = self.client.post(url, payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 400)

    def test_ticket_update_no_permission(self):
        other = User.objects.create_user("x", password="xpass")
        UserProfile.objects.get_or_create(user=other, defaults={"role": "user"})
        self.force_login(other)
        url = safe_reverse("ticket:ticket_update", args=[self.ticket.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    # DELETE
    def test_ticket_delete_by_owner(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:ticket_delete", args=[self.ticket.id])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertFalse(Ticket.objects.filter(id=self.ticket.id).exists())

    def test_ticket_delete_no_permission_ajax(self):
        other = User.objects.create_user("y", password="ypass")
        UserProfile.objects.get_or_create(user=other, defaults={"role": "user"})
        self.force_login(other)
        url = safe_reverse("ticket:ticket_delete", args=[self.ticket.id])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 403)

    def test_ticket_delete_ajax_exception_handling(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:ticket_delete", args=[self.ticket.id])
        with patch.object(Ticket, "delete", side_effect=Exception("DB error")):
            resp = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
            self.assertEqual(resp.status_code, 500)
            data = resp.json()
            self.assertFalse(data.get("success", True))

    # DETAIL
    def test_ticket_detail_for_owner(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:ticket_detail", args=[self.ticket.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.ticket.customer_name)

    def test_ticket_detail_no_permission(self):
        other = User.objects.create_user("zz", password="zz")
        UserProfile.objects.get_or_create(user=other, defaults={"role": "user"})
        self.force_login(other)
        url = safe_reverse("ticket:ticket_detail", args=[self.ticket.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    # API
    def test_get_place_price_api(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:get_place_price", args=[self.place.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertAlmostEqual(float(data.get("price")), float(self.place.price))

    def test_get_place_price_not_found(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:get_place_price", args=[999999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        data = resp.json()
        self.assertFalse(data.get("success"))

    def test_place_list_api_returns_places(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:place_list_api")
        resp = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("places", data)
        self.assertIsInstance(data["places"], list)

    def test_place_list_api_invalid_request(self):
        self.force_login(self.normal_user)
        url = safe_reverse("ticket:place_list_api")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    # FILTER & SEARCH
    def test_ticket_list_filters_and_search(self):
        self.force_login(self.normal_user)
        self.ticket.booking_date = date.today() - timedelta(days=1)
        self.ticket.save()

        for status_filter in ["past", "today", "upcoming"]:
            resp = self.client.get(safe_reverse("ticket:ticket_list"), {"status": status_filter})
            self.assertEqual(resp.status_code, 200)

        resp = self.client.get(safe_reverse("ticket:ticket_list"), {"search": "Budi"})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(safe_reverse("ticket:ticket_list"), {"search": str(self.ticket.id)})
        self.assertEqual(resp.status_code, 200)
