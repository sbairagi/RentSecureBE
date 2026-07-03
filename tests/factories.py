"""Factory re-exports — central access point for all test factories.

These are defined in the root-level conftest.py and re-exported here so
test modules can import them without triggering Django-heavy conftest
loading during collection from subdirectories.
"""

import importlib.util
from pathlib import Path

_ROOT_CONFTEST = (
    Path(__file__).resolve().parents[1] / "conftest.py"
    if (Path(__file__).resolve().parents[1] / "conftest.py").exists()
    else Path(__file__).resolve().parents[2] / "conftest.py"
)
_SPEC = importlib.util.spec_from_file_location("_root_conftest", _ROOT_CONFTEST)
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

AddOnPurchaseFactory = _MOD.AddOnPurchaseFactory
BuildingFactory = _MOD.BuildingFactory
CaretakerFactory = _MOD.CaretakerFactory
ExtraChargeFactory = _MOD.ExtraChargeFactory
NotificationPreferenceFactory = _MOD.NotificationPreferenceFactory
OwnerBankDetailsFactory = _MOD.OwnerBankDetailsFactory
PlanFeatureLimitFactory = _MOD.PlanFeatureLimitFactory
PropertyTaxRecordFactory = _MOD.PropertyTaxRecordFactory
RenterFactory = _MOD.RenterFactory
RentRecordFactory = _MOD.RentRecordFactory
RentRecordPaidFactory = _MOD.RentRecordPaidFactory
SubscriptionPlanFactory = _MOD.SubscriptionPlanFactory
UnitFactory = _MOD.UnitFactory
UsageLimitFactory = _MOD.UsageLimitFactory
UserFactory = _MOD.UserFactory
UserProfileFactory = _MOD.UserProfileFactory
UserSubscriptionFactory = _MOD.UserSubscriptionFactory

__all__ = [
    "UserFactory",
    "UserProfileFactory",
    "SubscriptionPlanFactory",
    "UserSubscriptionFactory",
    "PlanFeatureLimitFactory",
    "UsageLimitFactory",
    "BuildingFactory",
    "UnitFactory",
    "RenterFactory",
    "RentRecordFactory",
    "RentRecordPaidFactory",
    "CaretakerFactory",
    "ExtraChargeFactory",
    "PropertyTaxRecordFactory",
    "NotificationPreferenceFactory",
    "OwnerBankDetailsFactory",
    "AddOnPurchaseFactory",
]
