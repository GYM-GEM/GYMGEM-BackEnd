from decimal import Decimal, InvalidOperation
from authenticationAndAuthorization.permissions import HasRole
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import permission_classes
from .models import Payment
from utils.views import PaymobService, get_profile_id_from_token
from profiles.models import Profile
from courses.models import Course, CourseEnrollment

@permission_classes([HasRole(["Trainee","Trainer"])])
class StartPaymentAPIView(APIView):
    @extend_schema(
        tags=["Payment"],
        summary="Start payment",
        description="Initiate a Paymob payment and return an iframe URL",
        request={"type": "object", "properties": {"amount": {"type": "number"}, "course_id": {"type": "integer"}}, "required": ["amount"]},
        responses={201: {"type": "object", "properties": {"status": {"type": "string"}, "payment_id": {"type": "integer"}, "iframe_url": {"type": "string"}}}, 400: {"description": "Invalid amount"}, 404: {"description": "Profile or course not found"}},
    )
    def post(self, request):
        try:
            amount = request.data.get("amount")  # EGP
            amount_cents = int((Decimal(amount) * Decimal("100")).quantize(Decimal('1')))
        except (TypeError, ValueError, InvalidOperation):
            return Response({"status": "error", "code": "INVALID_AMOUNT", "detail": "Invalid amount"}, status=400)
        profile_id = get_profile_id_from_token(request)
        try:
            profile = Profile.objects.select_related('account').get(pk=profile_id)
        except Profile.DoesNotExist:
            return Response({"status": "error", "code": "PROFILE_NOT_FOUND", "detail": "Profile not found"}, status=404)

        # Optional: attach purpose to payment (e.g., course enrollment)
        course_id = request.data.get("course_id")
        course_obj = None
        if course_id is not None:
            try:
                course_obj = Course.objects.get(pk=int(course_id))
            except (ValueError, Course.DoesNotExist):
                return Response({"status": "error", "code": "COURSE_NOT_FOUND", "detail": "Course not found"}, status=404)
            # Enforce amount matches course price
            try:
                paid_amount = Decimal(amount).quantize(Decimal('0.01'))
                course_price = Decimal(course_obj.price).quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError):
                return Response({"status": "error", "code": "INVALID_AMOUNT", "detail": "Invalid amount"}, status=400)
            if paid_amount != course_price:
                return Response({
                    "status": "error",
                    "code": "AMOUNT_MISMATCH",
                    "detail": f"Amount must equal course price ({course_price}).",
                }, status=400)

        payment = Payment.objects.create(
            user=profile,
            amount=Decimal(amount),
            purpose_type=("course" if course_obj else None),
            purpose_id=(course_obj.id if course_obj else None),
        )

        auth_token = PaymobService.authenticate()
        order = PaymobService.create_order(auth_token, amount_cents)

        payment.paymob_order_id = order.get("id")
        payment.save()

        account = profile.account
        billing_data = {
            "first_name": getattr(account, 'first_name', None) or "NA",
            "last_name": getattr(account, 'last_name', None) or "NA",
            "email": getattr(account, 'email', None) or "NA",
            "phone_number": "+201000000000",
            "apartment": "NA",
            "floor": "NA",
            "street": "NA",
            "building": "NA",
            "city": "Cairo",
            "country": "EG",
            "state": "Cairo",
            "postal_code": "12345"
        }

        payment_token = PaymobService.create_payment_key(
            auth_token,
            order["id"],
            amount_cents,
            billing_data
        )

        iframe_url = (
            f"https://accept.paymob.com/api/acceptance/iframes/"
            f"{settings.PAYMOB_IFRAME_ID}"
            f"?payment_token={payment_token}"
        )

        return Response({
            "status": "ok",
            "payment_id": payment.id,
            "iframe_url": iframe_url
        }, status=201)


class PaymentStatusAPIView(APIView):
    permission_classes = [HasRole(["Trainee","Trainer"])]
    @extend_schema(
        tags=["Payment"],
        summary="Payment status",
        description="Get payment status by internal payment_id",
        responses={200: {"type": "object", "properties": {"payment_id": {"type": "integer"}, "status": {"type": "string"}, "paymob_order_id": {"type": "integer"}, "paymob_transaction_id": {"type": ["integer", "null"]}}}, 404: {"description": "Payment not found"}},
    )
    def get(self, request, payment_id: int):
        try:
            payment = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response({"status": "error", "code": "PAYMENT_NOT_FOUND", "detail": "Payment not found"}, status=404)

        return Response({
            "payment_id": payment.id,
            "status": payment.status,
            "paymob_order_id": payment.paymob_order_id,
            "paymob_transaction_id": payment.paymob_transaction_id,
        })


class PaymentRefreshAPIView(APIView):
    permission_classes = [HasRole(["Trainee","Trainer"])]
    @extend_schema(
        tags=["Payment"],
        summary="Refresh payment status",
        description="Optionally query Paymob to refresh status server-side without webhook",
        responses={200: {"type": "object", "properties": {"payment_id": {"type": "integer"}, "status": {"type": "string"}, "paymob_order_id": {"type": "integer"}, "paymob_transaction_id": {"type": ["integer", "null"]}}}, 404: {"description": "Payment not found"}},
    )
    def post(self, request, payment_id: int):
        try:
            payment = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response({"status": "error", "code": "PAYMENT_NOT_FOUND", "detail": "Payment not found"}, status=404)

        # Placeholder: If you want full server-side verification, implement a Paymob lookup here.
        # For now, simply return current stored status.
        return Response({
            "payment_id": payment.id,
            "status": payment.status,
            "paymob_order_id": payment.paymob_order_id,
            "paymob_transaction_id": payment.paymob_transaction_id,
        })


import hmac
import hashlib
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt


def _to_str(val):
    if isinstance(val, bool):
        return str(val).lower()
    if val is None:
        return ''
    return str(val)


def build_hmac_string(obj):
    # Build message per Paymob docs using defined field order
    keys = [
        'amount_cents', 'created_at', 'currency', 'error_occured', 'has_parent_transaction',
        'id', 'integration_id', 'is_3d_secure', 'is_auth', 'is_capture', 'is_refunded',
        'is_standalone_payment', 'is_voided', 'order', 'owner', 'pending', 'source_data_pan',
        'source_data_sub_type', 'source_data_type', 'success'
    ]
    parts = []
    for k in keys:
        v = obj.get(k)
        if k == 'order':
            v = obj.get('order', {}).get('id')
        parts.append(_to_str(v))
    return ''.join(parts)


def verify_hmac(obj, received_hmac):
    secret = settings.PAYMOB_HMAC_SECRET
    message = build_hmac_string(obj)
    calculated = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(calculated, received_hmac or '')


@csrf_exempt
@api_view(["POST"])
@extend_schema(
    tags=["Payment"],
    summary="Paymob webhook",
    description="Receive Paymob transaction updates and mark payments",
    responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}, 403: {"description": "Invalid HMAC"}},
)
def paymob_webhook(request):
    obj = request.data.get("obj", {})
    received_hmac = request.GET.get("hmac") or request.data.get('hmac')

    if not verify_hmac(obj, received_hmac):
        return Response({"status": "error", "code": "INVALID_HMAC", "detail": "Invalid HMAC"}, status=403)

    order_id = obj.get("order", {}).get("id")

    try:
        payment = Payment.objects.get(paymob_order_id=order_id)
    except Payment.DoesNotExist:
        return Response({"status": "error", "code": "PAYMENT_NOT_FOUND", "detail": "Payment not found"}, status=404)

    if obj.get("success") is True:
        payment.status = "paid"
        payment.paymob_transaction_id = obj.get("id")
        # If payment is for a course, enroll the user
        if payment.purpose_type == "course" and payment.purpose_id:
            try:
                course = Course.objects.get(pk=payment.purpose_id)
                # Avoid duplicate enrollment; if already enrolled, refund
                exists = CourseEnrollment.objects.filter(course=course, trainee_profile=payment.user).exists()
                if exists:
                    raise RuntimeError("ALREADY_ENROLLED")
                CourseEnrollment.objects.create(course=course, trainee_profile=payment.user, status="in_progress")
            except Exception:
                # Enrollment failed: Attempt refund
                try:
                    auth_token = PaymobService.authenticate()
                    amount_cents = int((Decimal(payment.amount) * Decimal("100")).quantize(Decimal('1')))
                    PaymobService.refund_transaction(auth_token, payment.paymob_transaction_id, amount_cents)
                    payment.status = "refunded"
                except Exception:
                    # Refund failed; keep status as paid but log outcome
                    payment.status = payment.status
    else:
        payment.status = "failed"

    payment.save()
    return Response({"status": "ok"})
