"""
Test suite for TailDown customer app.

Covers:
- 3 user groups (Customer, Staff, Manager) with distinct permissions
- Order CRUD (create via cart, edit, delete)
- Cross-user access denial
- Dashboard filtering by permission
- The deliverBy past-date edit persistence bug
- AJAX endpoints (order_edit_data, order_detail_data, OrderDeleteView, filterOrders)
- Cart add/delete/checkout flow

Run with:  python manage.py test customer
"""
from datetime import date, timedelta
import json

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from account.models import JobDetails
from customer.models import TailDownOrder, TailDownCart

User = get_user_model()


# Disable django-axes during tests so repeated logins don't get locked out.
@override_settings(AXES_ENABLED=False)
class TailDownBaseTestCase(TestCase):
    """
    Base class that sets up:
      - 3 groups: Customer, Staff, Manager
      - 3 users, one per group
      - A JobDetails record used by all orders
      - Helper methods for creating orders and logging in
    """

    @classmethod
    def setUpTestData(cls):
        # ---- Create the three groups with distinct permission sets ----
        taildown_ct = ContentType.objects.get_for_model(TailDownOrder)
        cart_ct = ContentType.objects.get_for_model(TailDownCart)

        # Grab the default Django CRUD permissions for TailDownOrder + TailDownCart
        def perms_for(ct, codenames):
            return list(Permission.objects.filter(content_type=ct, codename__in=codenames))

        view_all_perm = Permission.objects.get(
            content_type=taildown_ct, codename='view_all_taildownorders'
        )

        # Customer: can add/view/delete own cart, can view/change/delete own orders
        customer_group, _ = Group.objects.get_or_create(name='Customer')
        customer_group.permissions.set(
            perms_for(cart_ct, ['add_taildowncart', 'view_taildowncart', 'delete_taildowncart']) +
            perms_for(taildown_ct, ['view_taildownorder', 'change_taildownorder', 'delete_taildownorder'])
        )

        # Staff: same as Customer PLUS view_all_taildownorders (sees everyone's orders)
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        staff_group.permissions.set(
            perms_for(cart_ct, ['add_taildowncart', 'view_taildowncart', 'delete_taildowncart']) +
            perms_for(taildown_ct, ['view_taildownorder', 'change_taildownorder', 'delete_taildownorder']) +
            [view_all_perm]
        )

        # Manager: full permissions including view_all
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        manager_group.permissions.set(
            perms_for(cart_ct, ['add_taildowncart', 'view_taildowncart', 'change_taildowncart', 'delete_taildowncart']) +
            perms_for(taildown_ct, ['add_taildownorder', 'view_taildownorder', 'change_taildownorder', 'delete_taildownorder']) +
            [view_all_perm]
        )

        cls.customer_group = customer_group
        cls.staff_group = staff_group
        cls.manager_group = manager_group

        # ---- Create users ----
        # NOTE: custom User's is_active defaults to False, so we force it True.
        # UserManager.create_user only takes email/password, so set other fields manually.
        def make_user(email, first_name, phone, group):
            u = User(
                email=email,
                first_name=first_name,
                last_name='Test',
                company_name='ShowMotion Inc.',
                phone=phone,
                is_active=True,
                is_customer=True,
            )
            u.set_password('TestPass123!')
            u.save()
            u.groups.add(group)
            return u

        cls.customer_user = make_user('customer@test.com', 'Cathy', '1111111111', customer_group)
        cls.other_customer = make_user('other@test.com', 'Otto', '2222222222', customer_group)
        cls.staff_user = make_user('staff@test.com', 'Stan', '3333333333', staff_group)
        cls.manager_user = make_user('manager@test.com', 'Mandy', '4444444444', manager_group)

        # Superuser for "sees everything" tests
        cls.superuser = User(
            email='admin@test.com', first_name='Admin', last_name='Root',
            company_name='ShowMotion Inc.', phone='9999999999',
            is_active=True, is_staff=True, is_superuser=True, is_customer=True,
        )
        cls.superuser.set_password('TestPass123!')
        cls.superuser.save()

        # ---- Create a Job to attach orders to ----
        cls.job = JobDetails.objects.create(
            jobNo='J100', showName='Test Show', customer=cls.customer_user,
            createdBy=cls.superuser,
        )

    def setUp(self):
        self.client = Client()

    # ---- Helpers ----
    def login(self, user):
        """Force-login bypasses the login view (and avoids axes entirely)."""
        self.client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')

    def make_order(self, customer, order_name='Order 1', deliver_by=None, status='Ordered'):
        """Create a TailDownOrder directly in the DB (bypasses form validation)."""
        return TailDownOrder.objects.create(
            customer=customer,
            orderName=order_name,
            deliverBy=deliver_by or (date.today() + timedelta(days=30)),
            cableFinishes='GAL',
            cableSize='1/4"',
            cableLengthFt=10,
            cableLengthIn=0,
            showName=self.job,
            topType='Soft Eye',
            endType='Nico',
            turnbuckle=False,
            chain=False,
            tcOrder='none',
            turnbuckleSize='',
            chainLength='',
            quantity=2,
            status=status,
        )

    def valid_edit_post_data(self, deliver_by=None):
        """Returns a dict of valid POST data for TailDownOrderEditForm."""
        return {
            'orderName': 'Updated Order Name',
            'quantity': 3,
            'deliverBy': (deliver_by or (date.today() + timedelta(days=20))).strftime('%Y-%m-%d'),
            'showName': self.job.jobId,
            'cableSize': '1/4"',
            'cableFinishes': 'GAL',
            'cableLengthFt': 12,
            'cableLengthIn': 6,
            'topType': 'Soft Eye',
            'endType': 'Nico',
            'turnbuckle': False,
            'chain': False,
            'tcOrder': 'none',
            'turnbuckleSize': '',
            'chainLength': '',
            'status': 'Ordered',
        }


# =============================================================================
# Group & permission tests
# =============================================================================
class GroupSetupTests(TailDownBaseTestCase):
    def test_three_groups_exist(self):
        self.assertTrue(Group.objects.filter(name='Customer').exists())
        self.assertTrue(Group.objects.filter(name='Staff').exists())
        self.assertTrue(Group.objects.filter(name='Manager').exists())

    def test_customer_group_cannot_view_all_orders(self):
        self.assertFalse(self.customer_user.has_perm('customer.view_all_taildownorders'))

    def test_staff_group_can_view_all_orders(self):
        self.assertTrue(self.staff_user.has_perm('customer.view_all_taildownorders'))

    def test_manager_group_can_view_all_orders(self):
        self.assertTrue(self.manager_user.has_perm('customer.view_all_taildownorders'))

    def test_customer_has_basic_order_perms(self):
        self.assertTrue(self.customer_user.has_perm('customer.view_taildownorder'))
        self.assertTrue(self.customer_user.has_perm('customer.change_taildownorder'))
        self.assertTrue(self.customer_user.has_perm('customer.delete_taildownorder'))
        self.assertTrue(self.customer_user.has_perm('customer.add_taildowncart'))


# =============================================================================
# Dashboard tests — group-based visibility
# =============================================================================
class DashboardVisibilityTests(TailDownBaseTestCase):
    def setUp(self):
        super().setUp()
        self.own_order = self.make_order(self.customer_user, 'Cathy Order')
        self.other_order = self.make_order(self.other_customer, 'Otto Order')

    def test_customer_sees_only_own_orders(self):
        self.login(self.customer_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        orders = list(response.context['orders'])
        self.assertIn(self.own_order, orders)
        self.assertNotIn(self.other_order, orders)

    def test_staff_sees_all_orders(self):
        self.login(self.staff_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        orders = list(response.context['orders'])
        self.assertIn(self.own_order, orders)
        self.assertIn(self.other_order, orders)

    def test_manager_sees_all_orders(self):
        self.login(self.manager_user)
        response = self.client.get(reverse('dashboard'))
        orders = list(response.context['orders'])
        self.assertEqual(len(orders), 2)

    def test_superuser_sees_all_orders(self):
        self.login(self.superuser)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(len(list(response.context['orders'])), 2)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


# =============================================================================
# Order edit tests — INCLUDING THE PERSISTENCE BUG
# =============================================================================
class OrderEditTests(TailDownBaseTestCase):
    def setUp(self):
        super().setUp()
        self.order = self.make_order(self.customer_user, 'Original Name')

    def test_edit_persists_with_valid_data(self):
        """Baseline: a valid edit should actually update the DB."""
        self.login(self.customer_user)
        response = self.client.post(
            reverse('order_edit', args=[self.order.orderId]),
            self.valid_edit_post_data(),
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.orderName, 'Updated Order Name')
        self.assertEqual(self.order.quantity, 3)
        self.assertEqual(self.order.cableLengthFt, 12)

    def test_edit_fails_for_other_users_order(self):
        """A customer cannot edit another customer's order."""
        self.login(self.other_customer)
        response = self.client.post(
            reverse('order_edit', args=[self.order.orderId]),
            self.valid_edit_post_data(),
        )
        # get_queryset filters to own orders → 404
        self.assertEqual(response.status_code, 404)
        self.order.refresh_from_db()
        self.assertEqual(self.order.orderName, 'Original Name')  # unchanged

    def test_staff_can_edit_other_users_order(self):
        self.login(self.staff_user)
        response = self.client.post(
            reverse('order_edit', args=[self.order.orderId]),
            self.valid_edit_post_data(),
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.orderName, 'Updated Order Name')

    def test_edit_rejects_past_delivery_date(self):
        """A new past date should be rejected by form validation."""
        self.login(self.customer_user)
        past_date = date.today() - timedelta(days=5)
        response = self.client.post(
            reverse('order_edit', args=[self.order.orderId]),
            self.valid_edit_post_data(deliver_by=past_date),
        )
        self.order.refresh_from_db()
        # Edit should NOT have persisted
        self.assertEqual(self.order.orderName, 'Original Name')

    def test_BUG_cannot_edit_order_with_already_past_delivery_date(self):
        """
        THIS IS YOUR PERSISTENCE BUG.

        An order created with a deliverBy in the past cannot be edited at all,
        even if the user isn't changing deliverBy, because TailDownOrderEditForm
        re-validates the field and rejects any date < today.

        This test documents the bug. It will PASS as long as the bug exists.
        Once you fix the form, flip the assertion (see comments).
        """
        past_date = date.today() - timedelta(days=3)
        stale_order = self.make_order(
            self.customer_user, order_name='Stale', deliver_by=past_date
        )
        self.login(self.customer_user)

        # User submits an edit keeping the existing past date
        post_data = self.valid_edit_post_data(deliver_by=past_date)
        post_data['orderName'] = 'Should Persist'
        self.client.post(
            reverse('order_edit', args=[stale_order.orderId]),
            post_data,
        )
        stale_order.refresh_from_db()

        self.assertEqual(stale_order.orderName, 'Should Persist')

    def test_edit_rejects_invalid_quantity(self):
        self.login(self.customer_user)
        data = self.valid_edit_post_data()
        data['quantity'] = 50  # max is 25
        self.client.post(reverse('order_edit', args=[self.order.orderId]), data)
        self.order.refresh_from_db()
        self.assertNotEqual(self.order.quantity, 50)


# =============================================================================
# Order delete tests (AJAX)
# =============================================================================
class OrderDeleteTests(TailDownBaseTestCase):
    def setUp(self):
        super().setUp()
        self.order = self.make_order(self.customer_user)

    def test_customer_can_delete_own_order(self):
        self.login(self.customer_user)
        response = self.client.post(reverse('order_delete', args=[self.order.orderId]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertFalse(TailDownOrder.objects.filter(orderId=self.order.orderId).exists())

    def test_customer_cannot_delete_other_users_order(self):
        self.login(self.other_customer)
        response = self.client.post(reverse('order_delete', args=[self.order.orderId]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(TailDownOrder.objects.filter(orderId=self.order.orderId).exists())

    def test_staff_can_delete_any_order(self):
        self.login(self.staff_user)
        response = self.client.post(reverse('order_delete', args=[self.order.orderId]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TailDownOrder.objects.filter(orderId=self.order.orderId).exists())


# =============================================================================
# AJAX data endpoints
# =============================================================================
class OrderDataEndpointTests(TailDownBaseTestCase):
    def setUp(self):
        super().setUp()
        self.order = self.make_order(self.customer_user, 'Data Order')

    def test_order_edit_data_returns_json(self):
        self.login(self.customer_user)
        response = self.client.get(reverse('order_edit_data', args=[self.order.orderId]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['orderName'], 'Data Order')
        self.assertEqual(data['quantity'], 2)
        self.assertEqual(data['cableSize'], '1/4"')

    def test_order_edit_data_denies_other_user(self):
        self.login(self.other_customer)
        response = self.client.get(reverse('order_edit_data', args=[self.order.orderId]))
        self.assertEqual(response.status_code, 404)

    def test_order_detail_data_returns_json(self):
        self.login(self.customer_user)
        response = self.client.get(reverse('order_detail_data', args=[self.order.orderId]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['orderName'], 'Data Order')


# =============================================================================
# Filter orders endpoint
# =============================================================================
class FilterOrdersTests(TailDownBaseTestCase):
    def setUp(self):
        super().setUp()
        self.o1 = self.make_order(self.customer_user, 'Filter A')
        self.o2 = self.make_order(self.other_customer, 'Filter B')

    def test_customer_filter_returns_only_own(self):
        self.login(self.customer_user)
        response = self.client.post(
            reverse('filter_orders'),
            data=json.dumps({'show': '', 'deliverBy': ''}),
            content_type='application/json',
        )
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['orders'][0]['orderName'], 'Filter A')

    def test_staff_filter_returns_all(self):
        self.login(self.staff_user)
        response = self.client.post(
            reverse('filter_orders'),
            data=json.dumps({'show': '', 'deliverBy': ''}),
            content_type='application/json',
        )
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)


# =============================================================================
# Cart tests
# =============================================================================
class CartTests(TailDownBaseTestCase):
    def _valid_cart_post(self):
        return {
            'orderName': 'Cart Item',
            'quantity': 2,
            'deliverBy': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'showName': self.job.jobId,
            'cableFinishes': 'GAL',
            'cableSize': '1/4"',
            'cableLengthFt': 10,
            'cableLengthIn': 0,
            'topType': 'Soft Eye',
            'endType': 'Nico',
            'turnbuckle': False,
            'chain': False,
            'tcOrder': 'none',
            'turnbuckleSize': '',
            'chainLength': '',
        }

    def test_add_to_cart_creates_item(self):
        self.login(self.customer_user)
        response = self.client.post(reverse('customer_order'), self._valid_cart_post())
        self.assertEqual(response.status_code, 302)  # redirect on success
        self.assertEqual(
            TailDownCart.objects.filter(customer=self.customer_user, isOrdered=False).count(),
            1,
        )

    def test_add_to_cart_rejects_zero_quantity(self):
        self.login(self.customer_user)
        data = self._valid_cart_post()
        data['quantity'] = 0
        self.client.post(reverse('customer_order'), data)
        self.assertEqual(TailDownCart.objects.count(), 0)

    def test_add_to_cart_rejects_past_date(self):
        self.login(self.customer_user)
        data = self._valid_cart_post()
        data['deliverBy'] = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.client.post(reverse('customer_order'), data)
        self.assertEqual(TailDownCart.objects.count(), 0)

    def test_checkout_moves_cart_to_orders(self):
        self.login(self.customer_user)
        # Seed a cart item directly
        TailDownCart.objects.create(
            customer=self.customer_user, orderName='Checkout Me',
            deliverBy=date.today() + timedelta(days=30),
            cableFinishes='GAL', cableSize='1/4"',
            cableLengthFt=10, cableLengthIn=0,
            showName=self.job, topType='Soft Eye', endType='Nico',
            turnbuckle=False, chain=False, tcOrder='none',
            turnbuckleSize='', chainLength='', quantity=1,
        )
        response = self.client.post(reverse('customer_order_cart'))
        # Cart item marked ordered
        self.assertTrue(
            TailDownCart.objects.filter(customer=self.customer_user, isOrdered=True).exists()
        )
        # Permanent order created
        self.assertTrue(
            TailDownOrder.objects.filter(customer=self.customer_user, orderName='Checkout Me').exists()
        )

    def test_delete_cart_item_own(self):
        self.login(self.customer_user)
        cart_item = TailDownCart.objects.create(
            customer=self.customer_user, orderName='Delete Me',
            deliverBy=date.today() + timedelta(days=30),
            cableFinishes='GAL', cableSize='1/4"',
            cableLengthFt=10, cableLengthIn=0,
            showName=self.job, topType='Soft Eye', endType='Nico',
            turnbuckle=False, chain=False, tcOrder='none',
            turnbuckleSize='', chainLength='', quantity=1,
        )
        response = self.client.post(reverse('delete_cart_item', args=[cart_item.orderId]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TailDownCart.objects.filter(orderId=cart_item.orderId).exists())

    def test_delete_cart_item_denies_other_user(self):
        self.login(self.other_customer)
        cart_item = TailDownCart.objects.create(
            customer=self.customer_user, orderName='Not Yours',
            deliverBy=date.today() + timedelta(days=30),
            cableFinishes='GAL', cableSize='1/4"',
            cableLengthFt=10, cableLengthIn=0,
            showName=self.job, topType='Soft Eye', endType='Nico',
            turnbuckle=False, chain=False, tcOrder='none',
            turnbuckleSize='', chainLength='', quantity=1,
        )
        response = self.client.post(reverse('delete_cart_item', args=[cart_item.orderId]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(TailDownCart.objects.filter(orderId=cart_item.orderId).exists())