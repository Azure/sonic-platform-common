"""Endpoint page ownership and compatibility of the legacy combined map."""
import pytest

from sonic_platform_base.sonic_xcvr.codes.broadcom.bailly import BaillyCodes
from sonic_platform_base.sonic_xcvr.fields import consts
from sonic_platform_base.sonic_xcvr.fields.broadcom import bailly
from sonic_platform_base.sonic_xcvr.mem_maps.broadcom import bailly as legacy_module
from sonic_platform_base.sonic_xcvr.mem_maps.broadcom.bailly import BaillyMemMap
from sonic_platform_base.sonic_xcvr.mem_maps.broadcom.bailly_oe import BaillyOeMemMap
from sonic_platform_base.sonic_xcvr.mem_maps.broadcom.bailly_elsfp import BaillyElsfpMemMap
from sonic_platform_base.sonic_xcvr.mem_maps.public.cmis import CmisMemMap
from sonic_platform_base.sonic_xcvr.mem_maps.public.cmis.pages.page import CmisPage


@pytest.mark.parametrize("bank", [0, 1, 7])
def test_oe_map_keeps_public_cmis_pages_and_bank_addresses(bank):
    oe = BaillyOeMemMap(BaillyCodes, bank=bank)
    public = CmisMemMap(BaillyCodes, bank=bank)
    assert [(type(page), page.page, page.bank) for page in oe.pages] == [
        (type(page), page.page, page.bank) for page in public.pages
    ]
    assert oe.bank == bank
    assert oe.get_field(consts.TEMPERATURE_FIELD).get_offset() == public.get_field(
        consts.TEMPERATURE_FIELD).get_offset()
    assert oe.get_field(consts.TX_DISABLE_FIELD).get_offset() == CmisPage.linear_offset(0x10, bank, 130)
    for name in (bailly.CPO_INFO_FIELD, bailly.CPO_MODULE_MONITORS_FIELD, bailly.LASER_POWER_MODE_CONTROL_FIELD):
        with pytest.raises(KeyError):
            oe.get_field(name)


@pytest.mark.parametrize("bank", [0, 7])
@pytest.mark.parametrize("base_page", [0, 4])
def test_endpoint_maps_have_disjoint_pages_and_legacy_keeps_both(bank, base_page):
    oe = BaillyOeMemMap(BaillyCodes, bank=bank)
    els = BaillyElsfpMemMap(BaillyCodes, base_page=base_page)
    legacy = BaillyMemMap(BaillyCodes, bank=bank, base_page=base_page)
    oe_pages = {page.page for page in oe.pages}
    els_pages = {page.page for page in els.pages}
    assert els_pages == {0xB0 + base_page, 0xB1 + base_page, 0xB2 + base_page}
    assert oe_pages.isdisjoint(els_pages)
    assert {page.page for page in legacy.pages} == oe_pages | els_pages
    assert legacy.get_field(consts.TX_DISABLE_FIELD).get_offset() == oe.get_field(
        consts.TX_DISABLE_FIELD).get_offset()
    assert legacy.get_field(bailly.MODULE_TEMPERATURE_MONITOR).get_offset() == els.get_field(
        bailly.MODULE_TEMPERATURE_MONITOR).get_offset()


@pytest.mark.parametrize("base_page", [0, 4])
def test_legacy_and_endpoint_maps_own_independent_page_definitions(base_page):
    assert BaillyOeMemMap.__module__.endswith(".bailly_oe")
    assert BaillyElsfpMemMap.__module__.endswith(".bailly_elsfp")
    legacy = BaillyMemMap(BaillyCodes, base_page=base_page)
    els = BaillyElsfpMemMap(BaillyCodes, base_page=base_page)
    legacy_pages = {page.page: page for page in legacy.pages if page.page >= 0xB0}
    assert set(legacy_pages) == {page.page for page in els.pages}
    for page in els.pages:
        old_page = legacy_pages[page.page]
        assert type(old_page) is not type(page)
        assert type(old_page).__name__ == type(page).__name__
        assert type(old_page).__module__ == legacy_module.__name__
        assert type(page).__module__ == BaillyElsfpMemMap.__module__
    name = bailly.MODULE_TEMPERATURE_MONITOR
    assert legacy.get_field(name) is not els.get_field(name)
    assert legacy.get_field(name).get_offset() == els.get_field(name).get_offset()
