"""
AdSense Router: Serves /ads.txt for Google crawler compliance,
and endpoints for AdSense Publisher verification, account binding, and transaction resolution.
"""

from fastapi import APIRouter, Depends, Response, HTTPException, status
from api.dependencies import get_settings, verify_secure_access
from api.config import Settings
from api.schemas.adsense import (
    AdSenseResolveRequest,
    AdSenseResolveResponse,
    AdSenseStatusResponse,
    AdSenseLedgerResponse,
    AdSenseTransaction,
    AdSenseBindRequest,
    AdSenseBindResponse,
)
from api.services.adsense_service import AdSenseService

router = APIRouter(tags=["Google AdSense & Transactions"])

# Singleton service instance
_adsense_service: AdSenseService = AdSenseService()


def get_adsense_service() -> AdSenseService:
    return _adsense_service


@router.api_route("/ads.txt", methods=["GET", "HEAD"], summary="Serve Authorized Digital Sellers (ads.txt)")
async def ads_txt_endpoint(service: AdSenseService = Depends(get_adsense_service)):
    """
    Serves the RFC-compliant Authorized Digital Sellers (ads.txt) record
    for Google AdSense crawler verification at the domain root.
    """
    content = service.get_ads_txt_content()
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )


@router.get(
    "/api/adsense/status",
    dependencies=[Depends(verify_secure_access)],
    response_model=AdSenseStatusResponse,
    summary="AdSense Publisher Integration Status",
    description="Returns verified Publisher ID, ads.txt compliance, and transaction totals.",
)
async def adsense_status_endpoint(service: AdSenseService = Depends(get_adsense_service)) -> AdSenseStatusResponse:
    return service.get_status()


@router.get(
    "/api/adsense/ledger",
    dependencies=[Depends(verify_secure_access)],
    response_model=AdSenseLedgerResponse,
    summary="List received AdSense transactions",
    description="Returns the history of reconciled AdSense payout transactions.",
)
async def adsense_ledger_endpoint(service: AdSenseService = Depends(get_adsense_service)) -> AdSenseLedgerResponse:
    return service.get_ledger()


@router.post(
    "/api/adsense/bind",
    dependencies=[Depends(verify_secure_access)],
    response_model=AdSenseBindResponse,
    summary="Bind user Google AdSense Publisher Account",
    description="Updates publisher ID across ads.txt, knowledge specs, .env, and runtime.",
)
async def adsense_bind_endpoint(
    req: AdSenseBindRequest,
    service: AdSenseService = Depends(get_adsense_service),
) -> AdSenseBindResponse:
    res = service.bind_account(req.publisher_id, req.certification_authority_id)
    return AdSenseBindResponse(**res)


@router.post(
    "/api/adsense/transaction/resolve",
    dependencies=[Depends(verify_secure_access)],
    response_model=AdSenseResolveResponse,
    summary="Resolve and audit AdSense transaction receipt",
    description="Validates Publisher ID, parses payout metrics, and runs Gemini 3.8 audit assessment.",
)
async def adsense_resolve_endpoint(
    req: AdSenseResolveRequest,
    service: AdSenseService = Depends(get_adsense_service),
) -> AdSenseResolveResponse:
    return service.resolve_transaction(req)


@router.post(
    "/api/adsense/transaction/record",
    dependencies=[Depends(verify_secure_access)],
    response_model=AdSenseTransaction,
    summary="Record verified AdSense transaction",
    description="Persists a new AdSense transaction into the knowledge base ledger.",
)
async def adsense_record_endpoint(
    txn: AdSenseTransaction,
    service: AdSenseService = Depends(get_adsense_service),
) -> AdSenseTransaction:
    return service.record_transaction(txn)
