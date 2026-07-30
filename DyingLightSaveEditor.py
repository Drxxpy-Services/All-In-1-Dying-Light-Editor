from __future__ import annotations

import base64
import copy
import gzip
import hashlib
import json
import os
import queue
import re
import shutil
import struct
import subprocess
import tempfile
import threading
import time
import webbrowser
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET


APP_TITLE = "DYING LIGHT // SAVE ARCHITECT"
DEFAULT_SAVE = Path(
    r"D:\steam app\userdata\1168923626\239140\remote\out\save\save_coop_0.sav"
)
MAX_QUANTITY = 999_999
SOURCE_ARCHIVE = Path(r"D:\Ayden\Downloads\DyingLightSource-master.zip")
REFERENCE_SAVE_ARCHIVE = Path(r"D:\Ayden\Downloads\Save_all_dlc_100.zip")

# Verified from items that were absent in one checkpoint and created normally by
# the game in the next. Each tuple is (registry id, four-byte item metadata).
SPAWN_TEMPLATES = {
    "Craft_Alcohol": (269, bytes.fromhex("00d81c24")),
    "Craft_Gauze": (275, bytes.fromhex("0098110c")),
    "Craft_PlasticTube": (285, bytes.fromhex("0018906f")),
    "Craft_RazorBlade": (289, bytes.fromhex("00e82a49")),
    "Craft_String": (291, bytes.fromhex("00c0e47b")),
    "misc_cigarettes": (997, bytes.fromhex("000cde24")),
    "misc_coffee": (998, bytes.fromhex("0080a442")),
    "misc_pouch": (1003, bytes.fromhex("00c8de46")),
}
STACKABLE_TAIL = bytes.fromhex(
    "000080bf0000000000000000ffffffff000000000000ffffffff00"
)
EMBEDDED_REFERENCE_DATA = (
    "eNqFlttu4zYQht8l17ngUSJ7t/Fu00WTIEicDdCiEChqZKuRRUMHp7vFvnupGTnWNlbrKwPzcTT858S/L1atK/"
    "vsQ+3DNtQXP/0uEnt5wVjitdHs4o/LCbhyfQ9tBd2IpOzywlvDUsbmSA3Ob9HO0QVjVvOZPexyaH+tiga+IiVGqm"
    "A60e5EfRx8v3Z7QEKORKmUlTM/n2rwfRuaylMwaoSAqTxRJ+jaDd/Ihx7NMVgp9MzcAjQf6o0jJhmZiLB5JL8MTb"
    "zyde2aAqGUgtFFak/Q56aL0VS+KsiTubzILfcinytzU/ktNKPdsNGJUoXV5dy+2Y6fcnghg+oxDz4tTswt9K5+9K"
    "3bI4PacaZSNrvVnatqciHJhSpEfjLf166Loa6HHGM1qIxg2vJZrPfhFdqVy2tiUBnvi5zNLn3fVjtYV103EDQpI0H"
    "4GTT0LXQemv6mOkCLoEGdDTNqdvsH9y20V7UjBQ2Wn1Fpnsy++LhtQ9iNdosKJkZZnczsfVs1G7SjeoXRBZMz+7B"
    "xGIJF4Upv2TwB66pZOUyQxWoSJndsVgrr8Fflo3xNjwwKxxU4PRP/qSmgfXUxj291ZVG9RHnBZ86e9ps2Xja2FPab"
    "Tad0C5WehW4EYqidVVYxvoB9dKQQKqgVt8oskcMohmSMWqdgPHlPkjvJUFAX+31e9zOI7iEZKiuVtbw8yx0/SrVpv"
    "FDJEnd0eUwGJPositLErsV8eBNnwQJ2dJjQMACbwDI5ecW8OCZAiQX2eCNMjfZlKWGZnLxaiiD1Wv4X+xYGp3pXVi"
    "TJ/x7IVnXlX7DZJOfUbIVl5/JBoXNB3cS49mehSTguqQiKMnFnuSlYRd0ljeQL2NGhpmsp4H6ZnLxi1sCLOF4X2Kl"
    "WOeaMm0TrWSa+QBN2xzkuuZkGhBTYbz8PUF+FvseBp7Smb+XAMOs3wb/so6afexi/oJJx9RnvuaTteB/6KjTZ9Xao"
    "6W+EOEO5CsOsozXwOLSH6hDae+dfsjV0PVISv5WbhEkUdR2H3Os4ebPncYzcQj25w3FejNuJBs5v8SezlYv+2ri72"
    "11os5tDLcfu59SH0afVxXuYlmflV24DhE/NI71w7/FRnLVrXjIaQpxKnXmpKcE/0g+wCz3chmKg7cGpeB2TUpr3+C"
    "hEdtW6F+iyQ0IHUppIrNBq4cCnZlM1cDwgFK3ukku/cOCuiq+FA8UvEgooV8ot4A9ul9VHHK8rTdSdLeCPQ7eHphu"
    "LYAqJ0pp6lsti4dC6ak93VvQOiispXbrCemjz8MbThvQp4/Cef/pCoWtB+6LM5ZnQp+Z53gLQi4FrTJWPb4YfUhV2"
    "+9DEHZ7dDHksm2kDcp1QE3Gp1Dn6bui7q1D3k++UkpRLnZ+jH4Y8pxcC14bEM6mS59DHPkYcXzDTtud6WnYuTuGz"
    "/Nem30J89SCdTJeUknbPv+nnmBcCcXimynoxc3sLxUsVH4bg6n479vJ9C7tqwK0bt9nYpMykQs/Scurpx2EPsVPr0"
    "IfDeEBJSS+d+OCzpwO7qvPZnvxmPnS7MXiUUVHxxunDmF448Ce8TglVAkXPvS5TvkDvw0APdiWmvvaWtgxivoqPJo"
    "jv/tGhpXeKUqXi+oSEsgRAM3pwRiup3sxv4XBGY0kwnlI9UiBTANEsKY9xdEfz938A28LDFA=="
)
SAFE_TEMPLATE_CATEGORIES = {
    "CategoryType_Ammo",
    "CategoryType_Cash",
    "CategoryType_CraftComponent",
    "CategoryType_CraftPart",
    "CategoryType_Fuel",
    "CategoryType_Lockpick",
    "CategoryType_Medkit",
    "CategoryType_Powerup",
    "CategoryType_SurvivorPack",
    "CategoryType_Throwable",
    "CategoryType_ThrowableFlare",
    "CategoryType_ThrowableLiquid",
    "CategoryType_Valuable",
    "CategoryType_VehicleUpgrade",
}

COLORS = {
    "black": "#08090d",
    "panel": "#11131a",
    "panel_alt": "#191c25",
    "border": "#343844",
    "red": "#ff245d",
    "red_dark": "#b51646",
    "red_deep": "#560d29",
    "text": "#f8f8fb",
    "muted": "#a8a9b3",
    "success": "#3de0a0",
}

FRIENDLY_NAMES = {
    "Craft_Alcohol": "Alcohol",
    "Craft_DuctTape": "Duct Tape",
    "Craft_Electronics": "Electronics",
    "Craft_Gauze": "Gauze",
    "Craft_MetalScrap": "Metal Parts",
    "Craft_Nails": "Nails",
    "Craft_PlasticTube": "Plastic Tubing",
    "Craft_RazorBlade": "Razor Blades",
    "Craft_String": "String",
    "Craft_TinCan": "Tin Cans",
    "misc_cigarettes": "Cigarettes",
    "misc_coffee": "Coffee",
    "misc_pouch": "Pouch",
}

SOCKET_UPGRADES = [
    "None",
    "Craft_Upgrade_Dam",
    "Craft_Upgrade_Dur",
    "Craft_Upgrade_Bal",
    "Craft_Upgrade_DamDur",
    "Craft_Upgrade_DamBal",
    "Craft_Upgrade_DurBal",
    "Craft_Upgrade_DamDurBal",
    "Craft_Upgrade_DamL2",
    "Craft_Upgrade_DurL2",
    "Craft_Upgrade_BalL2",
    "Craft_Upgrade_DamL2DurL2",
    "Craft_Upgrade_DamL2BalL2",
    "Craft_Upgrade_DurL2BalL2",
    "Craft_Upgrade_DamL2DurL2BalL2",
    "Craft_Upgrade_DamL2Dur",
    "Craft_Upgrade_DamL2Bal",
    "Craft_Upgrade_DurL2Bal",
    "Craft_Upgrade_DurL2Dam",
    "Craft_Upgrade_BalL2Dam",
    "Craft_Upgrade_BalL2Dur",
    "Craftplan_GTFO20",
    "Craftplan_LightingRod",
    "Throwable_PoisonGrenade",
    "Craftplan_GodHammer",
    "Craftplan_AngelSword",
    "Craftplan_AllInOne",
    "Craftplan_ToxicReaper",
]


def load_source_item_catalog() -> list[tuple[str, str]]:
    items: dict[str, str] = {}
    if SOURCE_ARCHIVE.exists():
        try:
            with zipfile.ZipFile(SOURCE_ARCHIVE) as archive:
                for name in archive.namelist():
                    filename = Path(name).name.casefold()
                    if not (
                        filename.startswith("inventory")
                        and filename.endswith(".scr")
                    ):
                        continue
                    text = archive.read(name).decode("utf-8", errors="ignore")
                    for match in re.finditer(
                        r'\bItem\(\s*"([^"]+)"\s*,\s*(CategoryType_[A-Za-z0-9_]+)',
                        text,
                    ):
                        items.setdefault(match.group(1), match.group(2))
        except (OSError, zipfile.BadZipFile, KeyError):
            pass
    for identifier in SPAWN_TEMPLATES:
        items.setdefault(identifier, "CategoryType_CraftComponent")
    return sorted(items.items(), key=lambda item: item[0].casefold())


def load_source_item_details() -> dict[str, dict[str, object]]:
    details: dict[str, dict[str, object]] = {}
    if not SOURCE_ARCHIVE.exists():
        return details
    definition = re.compile(
        r'\bItem\(\s*"([^"]+)"\s*,\s*(CategoryType_[A-Za-z0-9_]+)\s*\)\s*\{'
    )
    property_pattern = re.compile(
        r"(?m)^\s*([A-Za-z][A-Za-z0-9_]*)\s*\(([^;\r\n]*)\)\s*;"
    )
    try:
        with zipfile.ZipFile(SOURCE_ARCHIVE) as archive:
            for name in archive.namelist():
                filename = Path(name).name.casefold()
                if not (
                    filename.startswith("inventory")
                    and filename.endswith(".scr")
                ):
                    continue
                text = archive.read(name).decode("utf-8", errors="ignore")
                for match in definition.finditer(text):
                    depth = 1
                    position = match.end()
                    while position < len(text) and depth:
                        if text[position] == "{":
                            depth += 1
                        elif text[position] == "}":
                            depth -= 1
                        position += 1
                    block = text[match.end() : max(match.end(), position - 1)]
                    properties: list[tuple[str, str]] = []
                    seen: set[tuple[str, str]] = set()
                    for prop in property_pattern.finditer(block):
                        pair = (prop.group(1), prop.group(2).strip())
                        if pair not in seen:
                            properties.append(pair)
                            seen.add(pair)
                    details.setdefault(
                        match.group(1),
                        {
                            "category": match.group(2),
                            "source": Path(name).name,
                            "properties": properties,
                        },
                    )
    except (OSError, zipfile.BadZipFile, KeyError):
        return {}
    return details


def load_source_skill_catalog() -> list[dict[str, object]]:
    skills: dict[str, dict[str, object]] = {}
    if not SOURCE_ARCHIVE.exists():
        return []
    pattern = re.compile(r"<skill\s+([^>]*\bid\s*=\s*\"[^\"]+\"[^>]*)>")
    attribute = re.compile(r"([A-Za-z_]+)\s*=\s*\"([^\"]*)\"")
    try:
        with zipfile.ZipFile(SOURCE_ARCHIVE) as archive:
            for name in archive.namelist():
                if not name.casefold().endswith("_skills.xml"):
                    continue
                text = archive.read(name).decode("utf-8", errors="ignore")
                for match in pattern.finditer(text):
                    attrs = dict(attribute.findall(match.group(1)))
                    identifier = attrs.get("id")
                    if not identifier:
                        continue
                    try:
                        max_level = max(1, int(attrs.get("max_level", "1")))
                        tier = int(attrs.get("tier", "0"))
                    except ValueError:
                        max_level, tier = 1, 0
                    skills.setdefault(
                        identifier,
                        {
                            "id": identifier,
                            "category": attrs.get("cat", "other").title(),
                            "max_level": max_level,
                            "tier": tier,
                            "points_type": attrs.get("skill_points_type", ""),
                            "source": Path(name).name,
                        },
                    )
    except (OSError, zipfile.BadZipFile, KeyError):
        return []
    return sorted(
        skills.values(),
        key=lambda skill: (
            str(skill["category"]).casefold(),
            int(skill["tier"]),
            str(skill["id"]).casefold(),
        ),
    )


def load_reference_spawn_templates(
    catalog: dict[str, str],
) -> dict[str, tuple[int, bytes]]:
    templates: dict[str, tuple[int, bytes]] = {}
    if not REFERENCE_SAVE_ARCHIVE.exists():
        return templates
    suffix = b"\x04\x00None" + (b"\x00" * 8)
    try:
        with zipfile.ZipFile(REFERENCE_SAVE_ARCHIVE) as archive:
            save_name = next(
                name for name in archive.namelist() if name.casefold().endswith(".sav")
            )
            decoded = gzip.decompress(archive.read(save_name))
    except (OSError, StopIteration, zipfile.BadZipFile, KeyError, EOFError):
        return {}
    for match in re.finditer(rb"[A-Za-z][A-Za-z0-9_]{2,}", decoded):
        start, end = match.span()
        if start < 6 or decoded[end : end + len(suffix)] != suffix:
            continue
        identifier = match.group().decode("ascii")
        if catalog.get(identifier) not in SAFE_TEMPLATE_CATEGORIES:
            continue
        if struct.unpack_from("<H", decoded, start - 2)[0] != len(identifier):
            continue
        registry_id = struct.unpack_from("<I", decoded, start - 6)[0]
        metadata_offset = end + len(suffix)
        metadata = decoded[metadata_offset : metadata_offset + 4]
        if len(metadata) == 4:
            templates.setdefault(identifier, (registry_id, metadata))
    return templates


def load_embedded_reference_templates() -> dict[str, tuple[int, bytes]]:
    try:
        payload = json.loads(
            zlib.decompress(base64.b64decode(EMBEDDED_REFERENCE_DATA)).decode("utf-8")
        )
        return {
            identifier: (int(values[0]), bytes.fromhex(values[1]))
            for identifier, values in payload.items()
        }
    except (ValueError, TypeError, KeyError, zlib.error):
        return {}


SOURCE_CATEGORY_INDEX = dict(load_source_item_catalog())
REFERENCE_SPAWN_TEMPLATES = {
    **load_embedded_reference_templates(),
    **load_reference_spawn_templates(SOURCE_CATEGORY_INDEX),
}
ALL_SPAWN_TEMPLATES = {**SPAWN_TEMPLATES, **REFERENCE_SPAWN_TEMPLATES}


class SaveFormatError(ValueError):
    pass


@dataclass(frozen=True)
class InventoryEntry:
    identifier: str
    quantity: int
    quantity_offset: int
    record_start: int
    record_end: int

    @property
    def display_name(self) -> str:
        if self.identifier in FRIENDLY_NAMES:
            return FRIENDLY_NAMES[self.identifier]
        name = re.sub(r"^(Craft_|misc_)", "", self.identifier)
        return re.sub(r"(?<!^)(?=[A-Z])", " ", name).replace("_", " ").title()


class DyingLightSave:
    """Reader/writer for the verified Dying Light 1 inventory record layout."""

    # Inventory records contain:
    # u16 identifier length, identifier, u16(4), "None", eight zero bytes,
    # four opaque bytes, then a little-endian u32 quantity.
    RECORD_SUFFIX = b"\x04\x00None" + (b"\x00" * 8)

    def __init__(self, path: Path, decoded: bytes):
        self.path = path
        self.decoded = bytearray(decoded)
        self.entries = self._find_inventory_entries()
        self.skills = self._find_skills()

    @classmethod
    def load(cls, path: Path) -> "DyingLightSave":
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise SaveFormatError(f"Could not read the save:\n{exc}") from exc
        if not raw.startswith(b"\x1f\x8b"):
            raise SaveFormatError("This file is not a Gzip-compressed Dying Light save.")
        try:
            decoded = gzip.decompress(raw)
        except (OSError, EOFError) as exc:
            raise SaveFormatError("The save is compressed but could not be decoded.") from exc
        if len(decoded) < 32 or decoded[:4] != b"\xff\xff\xff\xff":
            raise SaveFormatError("The decoded file does not match the expected save structure.")
        result = cls(path, decoded)
        if not result.entries:
            raise SaveFormatError("No supported inventory records were found in this save.")
        return result

    def _find_inventory_entries(self) -> list[InventoryEntry]:
        entries: list[InventoryEntry] = []
        data = bytes(self.decoded)
        # The same serialized record is used for crafting materials, valuables,
        # cash, consumables and many other existing inventory objects.
        identifier_pattern = re.compile(rb"[A-Za-z][A-Za-z0-9_]{2,}")

        for match in identifier_pattern.finditer(data):
            identifier_bytes = match.group()
            start, end = match.span()
            if start < 2:
                continue
            declared_length = struct.unpack_from("<H", data, start - 2)[0]
            if declared_length != len(identifier_bytes):
                continue
            if data[end : end + len(self.RECORD_SUFFIX)] != self.RECORD_SUFFIX:
                continue
            quantity_offset = end + len(self.RECORD_SUFFIX) + 4
            if quantity_offset + 4 > len(data):
                continue
            quantity = struct.unpack_from("<I", data, quantity_offset)[0]
            if quantity > MAX_QUANTITY:
                continue
            identifier = identifier_bytes.decode("ascii")
            record_start = start - 6
            # Verified stackable records have 55 bytes plus identifier length.
            record_end = record_start + len(identifier_bytes) + 55
            entries.append(
                InventoryEntry(
                    identifier, quantity, quantity_offset, record_start, record_end
                )
            )

        # The save may mention an identifier elsewhere; retain one editable record per item.
        unique: dict[str, InventoryEntry] = {}
        for entry in entries:
            unique[entry.identifier] = entry
        return sorted(unique.values(), key=lambda item: item.display_name.casefold())

    def _find_skills(self) -> list[str]:
        data = bytes(self.decoded)
        found = {
            match.group(1).decode("ascii")
            for match in re.finditer(rb"([A-Za-z][A-Za-z0-9_]{2,})_skill", data)
        }
        return sorted(found, key=str.casefold)

    def update_quantities(self, quantities: dict[str, int]) -> None:
        known = {entry.identifier: entry for entry in self.entries}
        for identifier, quantity in quantities.items():
            if identifier not in known:
                raise SaveFormatError(f"Inventory item disappeared: {identifier}")
            if not 0 <= quantity <= MAX_QUANTITY:
                raise SaveFormatError(
                    f"{known[identifier].display_name} must be between 0 and {MAX_QUANTITY:,}."
                )
            struct.pack_into("<I", self.decoded, known[identifier].quantity_offset, quantity)

    def spawn_supported_item(self, identifier: str, quantity: int) -> None:
        if not 1 <= quantity <= MAX_QUANTITY:
            raise SaveFormatError(f"Spawn quantity must be between 1 and {MAX_QUANTITY:,}.")
        existing = next(
            (entry for entry in self.entries if entry.identifier == identifier), None
        )
        if existing:
            struct.pack_into("<I", self.decoded, existing.quantity_offset, quantity)
            self.entries = self._find_inventory_entries()
            return
        if identifier not in ALL_SPAWN_TEMPLATES:
            raise SaveFormatError(
                "This item can be browsed, but its new-record metadata has not been "
                "verified yet. It cannot be safely spawned in this version."
            )

        registry_id, metadata = ALL_SPAWN_TEMPLATES[identifier]
        encoded_name = identifier.encode("ascii")
        record = (
            struct.pack("<I", registry_id)
            + struct.pack("<H", len(encoded_name))
            + encoded_name
            + self.RECORD_SUFFIX
            + metadata
            + struct.pack("<I", quantity)
            + STACKABLE_TAIL
        )

        # The active player inventory is the first dense run of serialized item
        # records. Later records are vehicle/loadout tables and must not be used.
        ordered = sorted(self.entries, key=lambda entry: entry.record_start)
        active: list[InventoryEntry] = []
        for entry in ordered:
            if not active or entry.record_start - active[-1].record_end < 256:
                active.append(entry)
            else:
                break
        if not active:
            raise SaveFormatError("Could not locate the active inventory section.")
        insertion_offset = active[-1].record_end

        marker = bytes(self.decoded).find(struct.pack("<I", 102), 0x400, insertion_offset)
        if marker < 0 or marker + 12 > insertion_offset:
            raise SaveFormatError("Could not locate the inventory size table.")
        first_size, second_size = struct.unpack_from("<II", self.decoded, marker + 4)
        if first_size - second_size != 4:
            raise SaveFormatError("Inventory size table failed validation.")

        self.decoded[insertion_offset:insertion_offset] = record
        struct.pack_into("<II", self.decoded, marker + 4, first_size + len(record), second_size + len(record))
        self.entries = self._find_inventory_entries()
        if not any(entry.identifier == identifier for entry in self.entries):
            raise SaveFormatError("The generated item record failed validation.")

    def spawn_catalog_item(self, identifier: str, category: str, quantity: int) -> None:
        """Create any source-catalogue item through the verified save serializer."""
        existing = next(
            (entry for entry in self.entries if entry.identifier == identifier), None
        )
        if existing:
            struct.pack_into("<I", self.decoded, existing.quantity_offset, quantity)
            self.entries = self._find_inventory_entries()
            return
        if identifier not in SOURCE_CATEGORY_INDEX:
            raise SaveFormatError("The selected identifier is not in the game-source catalogue.")
        if not 1 <= quantity <= MAX_QUANTITY:
            raise SaveFormatError(f"Spawn quantity must be between 1 and {MAX_QUANTITY:,}.")

        helper = Path(__file__).resolve().with_name("editor.exe")
        if not helper.exists():
            raise SaveFormatError(
                "Universal spawning requires editor.exe beside this Python file."
            )
        weapon_categories = {
            "CategoryType_Melee", "CategoryType_Firearm", "CategoryType_Bow",
            "CategoryType_Crossbow", "CategoryType_Weapon", "CategoryType_Shield",
        }
        with tempfile.TemporaryDirectory(prefix="dlse_spawn_") as folder:
            work = Path(folder)
            source = work / "source.sav"
            patch = work / "patch.json"
            output = work / "output.sav"
            source.write_bytes(gzip.compress(bytes(self.decoded), compresslevel=9, mtime=0))
            sampled = subprocess.run(
                [str(helper), "sample", f"--patch={patch}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if sampled.returncode or not patch.exists():
                raise SaveFormatError(
                    "The universal serializer could not decode this save revision."
                )
            data = json.loads(patch.read_text(encoding="utf-8"))
            inventory = data["player"]["inventory"]
            normal_items = inventory.get("items3", [])
            weapon_items = (
                inventory.get("items1", [])
                + inventory.get("quickSlots", [])
                + inventory.get("equipmentSlots", [])
            )
            donor_pool = weapon_items if category in weapon_categories else normal_items
            if not donor_pool:
                donor_pool = normal_items or weapon_items
            if not donor_pool:
                raise SaveFormatError("This save has no item record to use as an archetype.")
            all_items = normal_items + weapon_items
            used_ids = {int(item.get("id", 0)) for item in all_items}
            new_id = max(used_ids, default=0) + 1
            while new_id in used_ids:
                new_id += 1
            item = copy.deepcopy(donor_pool[0])
            item["id"] = new_id
            item["name"] = identifier
            item["quantity"] = quantity
            target = "items1" if category in weapon_categories else "items3"
            inventory.setdefault(target, []).append(item)
            patch.write_text(json.dumps(data), encoding="utf-8")
            updated = subprocess.run(
                [
                    str(helper), "update", f"--patch={patch}",
                    f"--output={output}", str(source),
                ],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if updated.returncode or not output.exists():
                raise SaveFormatError("The universal serializer rejected the new item.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
            if not any(entry.identifier == identifier for entry in self.entries):
                raise SaveFormatError("The generated item was not found after verification.")

    def spawn_all_catalog_items(self, quantity: int = 1) -> int:
        helper = Path(__file__).resolve().with_name("editor.exe")
        if not helper.exists():
            raise SaveFormatError("Universal spawning requires editor.exe beside this Python file.")
        weapon_categories = {
            "CategoryType_Melee", "CategoryType_Firearm", "CategoryType_Bow",
            "CategoryType_Crossbow", "CategoryType_Weapon", "CategoryType_Shield",
        }
        with tempfile.TemporaryDirectory(prefix="dlse_all_") as folder:
            work = Path(folder)
            source, patch, output = work / "source.sav", work / "patch.json", work / "output.sav"
            source.write_bytes(gzip.compress(bytes(self.decoded), compresslevel=9, mtime=0))
            result = subprocess.run(
                [str(helper), "sample", f"--patch={patch}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not patch.exists():
                raise SaveFormatError("The universal serializer could not decode this save.")
            data = json.loads(patch.read_text(encoding="utf-8"))
            inventory = data["player"]["inventory"]
            normal = inventory.get("items3", [])
            weapons = (
                inventory.get("items1", []) + inventory.get("quickSlots", [])
                + inventory.get("equipmentSlots", [])
            )
            if not normal and not weapons:
                raise SaveFormatError("This save has no item archetypes.")
            existing = {item.get("name") for item in normal + weapons}
            used_ids = {int(item.get("id", 0)) for item in normal + weapons}
            next_id = max(used_ids, default=0) + 1
            added = 0
            for identifier, category in load_source_item_catalog():
                if identifier in existing:
                    continue
                while next_id in used_ids:
                    next_id += 1
                donor_pool = weapons if category in weapon_categories else normal
                donor_pool = donor_pool or normal or weapons
                item = copy.deepcopy(donor_pool[0])
                item.update(id=next_id, name=identifier, quantity=quantity)
                inventory.setdefault(
                    "items1" if category in weapon_categories else "items3", []
                ).append(item)
                used_ids.add(next_id)
                existing.add(identifier)
                next_id += 1
                added += 1
            patch.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [str(helper), "update", f"--patch={patch}", f"--output={output}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not output.exists():
                raise SaveFormatError("The serializer rejected the complete item catalogue.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
            return added

    def spawn_named_inventory_items(
        self, identifiers: list[str], quantity: int = 1
    ) -> int:
        helper = Path(__file__).resolve().with_name("editor.exe")
        if not helper.exists():
            raise SaveFormatError("Item spawning requires editor.exe beside this file.")
        with tempfile.TemporaryDirectory(prefix="dlse_named_") as folder:
            work = Path(folder)
            source, patch, output = (
                work / "source.sav", work / "patch.json", work / "output.sav"
            )
            source.write_bytes(gzip.compress(bytes(self.decoded), compresslevel=9, mtime=0))
            result = subprocess.run(
                [str(helper), "sample", f"--patch={patch}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not patch.exists():
                raise SaveFormatError("The serializer could not decode this save.")
            data = json.loads(patch.read_text(encoding="utf-8"))
            inventory = data["player"]["inventory"]
            normal = inventory.get("items3", [])
            all_items = self._json_inventory_items(data)
            if not normal:
                raise SaveFormatError("No normal inventory archetype is available.")
            existing = {str(item.get("name", "")) for item in all_items}
            used_ids = {int(item.get("id", 0)) for item in all_items}
            next_id = max(used_ids, default=0) + 1
            added = 0
            for identifier in identifiers:
                if identifier in existing:
                    continue
                while next_id in used_ids:
                    next_id += 1
                item = copy.deepcopy(normal[0])
                item.update(id=next_id, name=identifier, quantity=quantity)
                normal.append(item)
                used_ids.add(next_id)
                existing.add(identifier)
                next_id += 1
                added += 1
            patch.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [str(helper), "update", f"--patch={patch}",
                 f"--output={output}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not output.exists():
                raise SaveFormatError("The serializer rejected the named item records.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
            return added

    def _serializer_json(self) -> tuple[Path, tempfile.TemporaryDirectory, dict]:
        helper = Path(__file__).resolve().with_name("editor.exe")
        if not helper.exists():
            raise SaveFormatError("Item editing requires editor.exe beside this Python file.")
        folder = tempfile.TemporaryDirectory(prefix="dlse_edit_")
        work = Path(folder.name)
        source, patch = work / "source.sav", work / "patch.json"
        source.write_bytes(gzip.compress(bytes(self.decoded), compresslevel=9, mtime=0))
        result = subprocess.run(
            [str(helper), "sample", f"--patch={patch}", str(source)],
            capture_output=True, text=True, creationflags=0x08000000,
        )
        if result.returncode or not patch.exists():
            folder.cleanup()
            raise SaveFormatError("The item serializer could not decode this save.")
        return helper, folder, json.loads(patch.read_text(encoding="utf-8"))

    def read_inspector_data(self) -> dict:
        """Return the serializer's complete nested representation of this save."""
        _helper, folder, data = self._serializer_json()
        folder.cleanup()
        return data

    @staticmethod
    def _json_inventory_items(data: dict) -> list[dict]:
        inventory = data["player"]["inventory"]
        return sum(
            (inventory.get(key, []) for key in
             ("items1", "items2", "items3", "quickSlots", "equipmentSlots")),
            [],
        )

    def read_item_attributes(self, identifier: str) -> dict:
        _helper, folder, data = self._serializer_json()
        try:
            item = next(
                (obj for obj in self._json_inventory_items(data)
                 if obj.get("name") == identifier),
                None,
            )
            if item is None:
                raise SaveFormatError("The selected item was not found by the serializer.")
            return copy.deepcopy(item)
        finally:
            folder.cleanup()

    def update_item_attributes(self, identifier: str, values: dict) -> None:
        helper, folder, data = self._serializer_json()
        try:
            item = next(
                (obj for obj in self._json_inventory_items(data)
                 if obj.get("name") == identifier),
                None,
            )
            if item is None:
                raise SaveFormatError("The selected item was not found by the serializer.")
            item["quantity"] = int(values["quantity"])
            item["condition"] = float(values["condition"])
            item["repairs"] = int(values["repairs"])
            item["craftPlan"] = values["craftPlan"] or "None"
            item["upgradeSockets"] = values["upgradeSockets"]
            item.setdefault("attributes", {})["color"] = values["color"]
            item.setdefault("unknown", {})["unknown008"] = int(values["power"])
            work = Path(folder.name)
            source, patch, output = (
                work / "source.sav", work / "patch.json", work / "output.sav"
            )
            patch.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [str(helper), "update", f"--patch={patch}",
                 f"--output={output}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not output.exists():
                raise SaveFormatError("The serializer rejected these item values.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
        finally:
            folder.cleanup()

    def repair_all_weapon_power_values(self) -> int:
        helper, folder, data = self._serializer_json()
        try:
            inventory = data["player"]["inventory"]
            weapons = sum(
                (
                    inventory.get(key, [])
                    for key in ("items1", "quickSlots", "equipmentSlots")
                ),
                [],
            )
            changed = 0
            for item in weapons:
                name = str(item.get("name", ""))
                category = SOURCE_CATEGORY_INDEX.get(name, "")
                is_weapon = category in {
                    "CategoryType_Melee", "CategoryType_Firearm",
                    "CategoryType_Bow", "CategoryType_Crossbow",
                    "CategoryType_Weapon",
                }
                if not is_weapon:
                    continue
                current = int(item.get("unknown", {}).get("unknown008", -1))
                if -1 <= current <= 255:
                    continue
                # unknown008 is a tightly constrained runtime weapon value, not
                # raw damage. The previously verified value 8 preserves firearm
                # behavior; huge values can prevent weapons from firing.
                item.setdefault("unknown", {})["unknown008"] = 8
                changed += 1
            if not changed:
                raise SaveFormatError(
                    "No recognized weapons were found in the active inventory."
                )
            work = Path(folder.name)
            source, patch, output = (
                work / "source.sav", work / "patch.json", work / "output.sav"
            )
            patch.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [str(helper), "update", f"--patch={patch}",
                 f"--output={output}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not output.exists():
                raise SaveFormatError("The serializer rejected the weapon repair.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
            return changed
        finally:
            folder.cleanup()

    def read_skill_levels(self) -> dict[str, int]:
        _helper, folder, data = self._serializer_json()
        try:
            levels: dict[str, int] = {}
            player = data.get("player", {})
            for skill in player.get("skills", []):
                identifier = str(skill.get("name", ""))
                levels[identifier] = int(
                    skill.get("unknown", {}).get("unknown001", 1)
                )
            for buff in player.get("buffs", []):
                name = str(buff.get("name", ""))
                if name.endswith("_skill"):
                    levels[name[:-6]] = int(buff.get("stacks", 1))
            return levels
        finally:
            folder.cleanup()

    def update_skill_levels(self, changes: dict[str, int]) -> None:
        helper, folder, data = self._serializer_json()
        try:
            player = data.setdefault("player", {})
            skills = player.setdefault("skills", [])
            buffs = player.setdefault("buffs", [])
            skill_map = {str(item.get("name", "")): item for item in skills}
            buff_map = {
                str(item.get("name", ""))[:-6]: item
                for item in buffs
                if str(item.get("name", "")).endswith("_skill")
            }
            for identifier, level in changes.items():
                if level <= 0:
                    skills[:] = [
                        item for item in skills if item.get("name") != identifier
                    ]
                    buffs[:] = [
                        item for item in buffs
                        if item.get("name") != f"{identifier}_skill"
                    ]
                    continue
                skill = skill_map.get(identifier)
                if skill is None:
                    skill = {
                        "name": identifier,
                        "unknown": {
                            "unknown001": level,
                            "unknown002": 0,
                            "unknown003": 0,
                        },
                    }
                    skills.append(skill)
                skill.setdefault("unknown", {})["unknown001"] = level
                buff = buff_map.get(identifier)
                if buff is None:
                    buff = {"name": f"{identifier}_skill", "stacks": level}
                    buffs.append(buff)
                buff["stacks"] = level
            work = Path(folder.name)
            source, patch, output = (
                work / "source.sav", work / "patch.json", work / "output.sav"
            )
            patch.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [str(helper), "update", f"--patch={patch}",
                 f"--output={output}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not output.exists():
                raise SaveFormatError("The serializer rejected these skill changes.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
            self.skills = self._find_skills()
        finally:
            folder.cleanup()

    def read_player_progression(self) -> dict[str, float | int]:
        _helper, folder, data = self._serializer_json()
        try:
            player = data.get("player", {})
            inventory = player.get("inventory", {})
            storage = player.get("storage", {})
            daytime = data.get("daytime", {})
            return {
                "health": float(player.get("health", 0)),
                "fury": float(player.get("fury", 0)),
                "cash": int(inventory.get("cash", 0)),
                "storage_cash": int(storage.get("cash", 0)),
                "days_elapsed": int(daytime.get("daysElapsed", 0)),
                "time_of_day": float(daytime.get("timeOfDay", 0)),
            }
        finally:
            folder.cleanup()

    def update_player_progression(self, values: dict[str, float | int]) -> None:
        helper, folder, data = self._serializer_json()
        try:
            player = data.setdefault("player", {})
            inventory = player.setdefault("inventory", {})
            storage = player.setdefault("storage", {})
            daytime = data.setdefault("daytime", {})
            player["health"] = float(values["health"])
            player["fury"] = float(values["fury"])
            inventory["cash"] = int(values["cash"])
            storage["cash"] = int(values["storage_cash"])
            daytime["daysElapsed"] = int(values["days_elapsed"])
            daytime["timeOfDay"] = float(values["time_of_day"])
            work = Path(folder.name)
            source, patch, output = (
                work / "source.sav", work / "patch.json", work / "output.sav"
            )
            patch.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [str(helper), "update", f"--patch={patch}",
                 f"--output={output}", str(source)],
                capture_output=True, text=True, creationflags=0x08000000,
            )
            if result.returncode or not output.exists():
                raise SaveFormatError("The serializer rejected these progression values.")
            self.decoded = bytearray(gzip.decompress(output.read_bytes()))
            self.entries = self._find_inventory_entries()
            self.skills = self._find_skills()
        finally:
            folder.cleanup()

    def write_safely(self) -> Path:
        # Decode our own output before replacing the source.
        encoded = gzip.compress(bytes(self.decoded), compresslevel=6, mtime=0)
        if gzip.decompress(encoded) != bytes(self.decoded):
            raise SaveFormatError("Internal verification failed; the save was not written.")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = self.path.parent / "DLSE Backups"
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / f"{self.path.stem}_{timestamp}{self.path.suffix}.bak"
        counter = 1
        while backup.exists():
            backup = backup_dir / (
                f"{self.path.stem}_{timestamp}-{counter}{self.path.suffix}.bak"
            )
            counter += 1
        shutil.copy2(self.path, backup)

        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{self.path.stem}_",
                suffix=".tmp",
                dir=self.path.parent,
                delete=False,
            ) as temp:
                temp.write(encoded)
                temp.flush()
                os.fsync(temp.fileno())
                temp_name = temp.name
            os.replace(temp_name, self.path)
        except Exception:
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            raise
        return backup


class SaveEditorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x720")
        self.minsize(780, 560)
        self.configure(bg=COLORS["black"])
        self.save: DyingLightSave | None = None
        self.quantity_vars: dict[str, tk.StringVar] = {}
        self.status_var = tk.StringVar(value="Open a Dying Light 1 Steam save to begin.")
        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.inventory_category_var = tk.StringVar(value="All categories")
        self.item_catalog = load_source_item_catalog()
        self.item_details = load_source_item_details()
        self.skill_catalog = load_source_skill_catalog()
        self._configure_theme()
        self._build_ui()
        # Windowed fullscreen: maximized with the native title bar preserved.
        try:
            self.state("zoomed")
        except tk.TclError:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            self.geometry(f"{screen_width}x{screen_height}+0+0")
        if DEFAULT_SAVE.exists():
            self.open_save(DEFAULT_SAVE)

    def _configure_theme(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 11))
        style.configure("App.TFrame", background=COLORS["black"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure(
            "App.TLabel", background=COLORS["black"], foreground=COLORS["text"]
        )
        style.configure(
            "Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"]
        )
        style.configure(
            "Muted.TLabel", background=COLORS["black"], foreground=COLORS["muted"]
        )
        style.configure(
            "Heading.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["red"],
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "TButton",
            background=COLORS["panel_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            focusthickness=0,
            padding=(15, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "TButton",
            background=[("active", COLORS["red_dark"]), ("pressed", COLORS["red_deep"])],
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["red"],
            foreground="white",
            bordercolor=COLORS["red"],
            font=("Segoe UI Bold", 10),
            padding=(20, 12),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#f02b55"), ("pressed", COLORS["red_dark"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["panel_alt"],
            foreground=COLORS["text"],
            insertcolor=COLORS["red"],
            bordercolor=COLORS["border"],
            padding=10,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Vertical.TScrollbar",
            background=COLORS["red_dark"],
            troughcolor=COLORS["panel"],
            bordercolor=COLORS["panel"],
            arrowcolor=COLORS["text"],
        )
        style.configure("TSeparator", background=COLORS["border"])
        style.configure(
            "Treeview",
            background=COLORS["panel"],
            fieldbackground=COLORS["panel"],
            foreground=COLORS["text"],
            rowheight=40,
            bordercolor=COLORS["border"],
            font=("Segoe UI", 10),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["red_dark"])],
            foreground=[("selected", "white")],
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["panel_alt"],
            foreground=COLORS["red"],
            relief="flat",
            font=("Segoe UI Bold", 9),
            padding=(10, 12),
        )

    @staticmethod
    def _mix_color(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> str:
        rgb = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _paint_gradient(self, event: tk.Event | None = None) -> None:
        width = max(1, self.banner.winfo_width())
        height = max(1, self.banner.winfo_height())
        self.banner.delete("gradient")
        start, middle, end = (5, 5, 8), (70, 8, 24), (225, 29, 72)
        steps = min(width, 320)
        for index in range(steps):
            t = index / max(1, steps - 1)
            if t < 0.58:
                color = self._mix_color(start, middle, t / 0.58)
            else:
                color = self._mix_color(middle, end, (t - 0.58) / 0.42)
            x1 = round(index * width / steps)
            x2 = round((index + 1) * width / steps) + 1
            self.banner.create_rectangle(
                x1, 0, x2, height, fill=color, outline=color, tags="gradient"
            )
        self.banner.tag_lower("gradient")
        if hasattr(self, "banner_button_window"):
            self.banner.coords(self.banner_button_window, width - 24, height // 2)

    def _build_ui(self) -> None:
        self.columnconfigure(0, minsize=236)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)

        self.banner = tk.Canvas(
            self, height=118, bg=COLORS["black"], highlightthickness=0
        )
        self.banner.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.banner.bind("<Configure>", self._paint_gradient)
        self.banner.create_text(
            24,
            35,
            anchor="nw",
            text=APP_TITLE,
            fill="white",
            font=("Segoe UI Black", 25),
        )
        self.banner.create_text(
            26,
            79,
            anchor="nw",
            text="STEAM SAVE CONTROL SYSTEM   •   DYING LIGHT 1",
            fill="#e6cbd2",
            font=("Segoe UI Bold", 9),
        )
        open_button = ttk.Button(
            self.banner, text="OPEN SAVE", command=self.choose_save, style="Accent.TButton"
        )
        self.banner_button_window = self.banner.create_window(
            940, 56, window=open_button, anchor="e"
        )

        self.sidebar = tk.Frame(
            self, bg="#09070b", width=236, highlightbackground=COLORS["border"],
            highlightthickness=1
        )
        self.sidebar.grid(row=1, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_propagate(False)
        tk.Label(
            self.sidebar, text="SAVE ARCHITECT", bg=COLORS["red_deep"], fg="white",
            font=("Segoe UI Bold", 10), anchor="w", padx=20, pady=16
        ).pack(fill="x")
        self.nav_buttons: dict[str, tk.Button] = {}
        nav_items = [
            ("dashboard", "⌂", "Dashboard"),
            ("inventory", "▦", "Inventory"),
            ("spawner", "✦", "Item Spawner"),
            ("skills", "◆", "Skills"),
            ("progression", "▲", "Player Progression"),
            ("devtools", "⚡", "Developer Tools"),
            ("runtime", "▶", "Runtime Mods"),
            ("cheatengine", "⌁", "Cheat Engine"),
            ("inspector", "{ }", "Save Inspector"),
            ("backups", "◫", "Backups"),
            ("about", "●", "About Us"),
        ]
        for key, icon, label in nav_items:
            button = tk.Button(
                self.sidebar,
                text=f"  {icon}   {label}",
                command=lambda selected=key: self.show_page(selected),
                bg="#09070b",
                fg="#d9dae1",
                activebackground=COLORS["red_deep"],
                activeforeground="white",
                relief="flat",
                bd=0,
                anchor="w",
                padx=20,
                pady=15,
                font=("Segoe UI Semibold", 10),
                cursor="hand2",
            )
            button.pack(fill="x")
            self.nav_buttons[key] = button
        tk.Frame(self.sidebar, bg=COLORS["border"], height=1).pack(
            fill="x", padx=16, pady=12
        )
        tk.Label(
            self.sidebar,
            text="●  SAFE WRITE MODE\n    Automatic backups enabled",
            bg="#09070b",
            fg=COLORS["success"],
            justify="left",
            anchor="w",
            padx=18,
            font=("Segoe UI Semibold", 8),
        ).pack(fill="x")

        path_frame = ttk.Frame(self, padding=(20, 12, 20, 8), style="App.TFrame")
        path_frame.grid(row=1, column=1, sticky="ew")
        path_frame.columnconfigure(0, weight=1)
        ttk.Label(
            path_frame, text="ACTIVE SAVE FILE", style="Muted.TLabel",
            font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Label(
            path_frame, text="●  CONNECTED", style="Muted.TLabel",
            foreground=COLORS["success"], font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=1, sticky="e", pady=(0, 5))
        ttk.Entry(path_frame, textvariable=self.path_var, state="readonly").grid(
            row=1, column=0, sticky="ew"
        )
        ttk.Button(path_frame, text="RELOAD SAVE", command=self.reload_save).grid(
            row=1, column=1, padx=(8, 0)
        )

        self.toolbar = ttk.Frame(self, padding=(20, 4, 20, 12), style="App.TFrame")
        self.toolbar.grid(row=2, column=1, sticky="ew")
        self.toolbar.columnconfigure(2, weight=1)
        tk.Frame(self.toolbar, bg=COLORS["red"], width=5, height=30).grid(
            row=0, column=0, sticky="ns", padx=(0, 12)
        )
        self.page_title = ttk.Label(
            self.toolbar, text="DASHBOARD", style="App.TLabel",
            font=("Segoe UI Black", 15)
        )
        self.page_title.grid(
            row=0, column=1, sticky="w", padx=(0, 24)
        )
        self.search_entry = ttk.Entry(self.toolbar, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=2, sticky="ew")
        self.search_var.trace_add("write", lambda *_args: self._show_entries())
        self.inventory_categories = sorted(
            {
                category.replace("CategoryType_", "")
                for _identifier, category in self.item_catalog
            },
            key=str.casefold,
        )
        self.max_button = ttk.Button(
            self.toolbar, text="MAX VISIBLE", command=self.max_visible
        )
        self.max_button.grid(
            row=0, column=3, padx=(10, 0)
        )
        self.reset_button = ttk.Button(
            self.toolbar, text="RESET", command=self.reset_values
        )
        self.reset_button.grid(
            row=0, column=4, padx=(8, 0)
        )

        self.page_host = ttk.Frame(self, padding=(20, 0, 20, 0), style="App.TFrame")
        self.page_host.grid(row=3, column=1, sticky="nsew")
        self.page_host.columnconfigure(0, weight=1)
        self.page_host.rowconfigure(0, weight=1)
        self.pages: dict[str, tk.Widget] = {}

        inventory_page = ttk.Frame(self.page_host, style="Panel.TFrame")
        inventory_page.columnconfigure(0, weight=1)
        inventory_page.rowconfigure(0, weight=1)
        self.pages["inventory"] = inventory_page
        self.canvas = tk.Canvas(
            inventory_page, highlightthickness=1, highlightbackground=COLORS["border"],
            bg=COLORS["panel"]
        )
        scrollbar = ttk.Scrollbar(
            inventory_page, orient="vertical", command=self.canvas.yview
        )
        self.items_frame = ttk.Frame(self.canvas, style="Panel.TFrame")
        self.items_window = self.canvas.create_window(
            (0, 0), window=self.items_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.items_frame.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.items_window, width=event.width),
        )
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda event: self.canvas.yview_scroll(int(-event.delta / 120), "units"),
        )
        ttk.Label(
            self.items_frame,
            text="No save loaded.",
            style="Panel.TLabel",
            padding=18,
        ).grid(row=0, column=0)

        self._build_information_pages()
        self._build_spawner_page()

        footer = ttk.Frame(self, padding=(20, 12, 20, 16), style="App.TFrame")
        footer.grid(row=4, column=1, sticky="ew")
        footer.columnconfigure(1, weight=1)
        tk.Label(
            footer, text="READY", bg="#12231d", fg=COLORS["success"],
            font=("Segoe UI Semibold", 8), padx=10, pady=5,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Label(
            footer,
            textvariable=self.status_var,
            wraplength=520,
            style="Muted.TLabel",
            font=("Segoe UI", 9),
        ).grid(row=0, column=1, sticky="w")
        self.save_button = ttk.Button(
            footer, text="SAVE CHANGES", command=self.save_changes,
            state="disabled", style="Accent.TButton"
        )
        self.save_button.grid(row=0, column=2, padx=(12, 0))
        self.show_page("dashboard")

    def _build_information_pages(self) -> None:
        definitions = {
            "dashboard": (
                "SAVE OVERVIEW",
                "Open a Dying Light save to view its decoded size, inventory records, "
                "unlocked skills, location data, and safety status.",
            ),
            "skills": (
                "UNLOCKED SKILLS",
                "Skills detected from the authoritative game identifiers will appear here. "
                "Skill writing remains locked until its complete record layout is verified.",
            ),
            "progression": (
                "PLAYER PROGRESSION",
                "Runner, Fighter, Survivor and Legend progression fields are being mapped. "
                "This page is read-only to protect the save from invalid XP combinations.",
            ),
            "devtools": (
                "DEVELOPER TOOLS",
                "Save-compatible tools adapted from the supplied developer menus. "
                "Every change is staged and protected by the normal backup system.",
            ),
            "runtime": (
                "RUNTIME MODS",
                "Install and manage in-game features that cannot be stored in a save file.",
            ),
            "cheatengine": (
                "CHEAT ENGINE",
                "Build and launch a Dying Light cheat table with automatic process attachment.",
            ),
            "inspector": (
                "SAVE INSPECTOR",
                "Technical save details, decoded identifiers, compression status and file "
                "fingerprint appear here after loading.",
            ),
            "backups": (
                "AUTOMATIC BACKUPS",
                "Every write creates a timestamped backup in the “DLSE Backups” folder "
                "beside the original save.",
            ),
            "about": (
                "ABOUT US",
                "The people behind Dying Light // Save Architect.",
            ),
        }
        self.info_bodies: dict[str, tk.Text] = {}
        for key, (title, description) in definitions.items():
            page = tk.Frame(
                self.page_host, bg=COLORS["panel"],
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            self.pages[key] = page
            tk.Label(
                page, text=title, bg=COLORS["panel"], fg=COLORS["red"],
                font=("Segoe UI Black", 18), anchor="w"
            ).pack(fill="x", padx=28, pady=(28, 8))
            tk.Label(
                page, text=description, bg=COLORS["panel"], fg=COLORS["muted"],
                font=("Segoe UI", 10), justify="left", anchor="w", wraplength=650
            ).pack(fill="x", padx=28)
            if key == "skills":
                controls = tk.Frame(page, bg=COLORS["panel"])
                controls.pack(fill="x", padx=28, pady=(20, 10))
                controls.columnconfigure(0, weight=1)
                self.skill_search_var = tk.StringVar()
                self.skill_category_var = tk.StringVar(value="All trees")
                self.skill_rank_var = tk.StringVar(value="1")
                ttk.Entry(
                    controls, textvariable=self.skill_search_var
                ).grid(row=0, column=0, sticky="ew")
                skill_trees = sorted(
                    {str(skill["category"]) for skill in self.skill_catalog},
                    key=str.casefold,
                )
                skill_category = ttk.Combobox(
                    controls, textvariable=self.skill_category_var,
                    values=["All trees", *skill_trees],
                    state="readonly", width=20,
                )
                skill_category.grid(row=0, column=1, padx=(10, 0))
                ttk.Label(
                    controls, text="Rank", style="Panel.TLabel"
                ).grid(row=0, column=2, padx=(14, 6))
                ttk.Entry(
                    controls, textvariable=self.skill_rank_var,
                    width=7, justify="right",
                ).grid(row=0, column=3)
                self.skill_search_var.trace_add(
                    "write", lambda *_args: self._refresh_skill_tree()
                )
                skill_category.bind(
                    "<<ComboboxSelected>>",
                    lambda _event: self._refresh_skill_tree(),
                )

                table = tk.Frame(page, bg=COLORS["panel"])
                table.pack(fill="both", expand=True, padx=28)
                table.columnconfigure(0, weight=1)
                table.rowconfigure(0, weight=1)
                self.skill_tree = ttk.Treeview(
                    table,
                    columns=("skill", "tree", "tier", "rank", "maximum", "status"),
                    show="headings", selectmode="extended",
                )
                for column, heading, width, anchor in (
                    ("skill", "SKILL", 390, "w"),
                    ("tree", "TREE", 130, "w"),
                    ("tier", "TIER", 70, "center"),
                    ("rank", "RANK", 70, "center"),
                    ("maximum", "MAX", 70, "center"),
                    ("status", "STATUS", 110, "center"),
                ):
                    self.skill_tree.heading(column, text=heading)
                    self.skill_tree.column(column, width=width, anchor=anchor)
                skill_scroll = ttk.Scrollbar(
                    table, orient="vertical", command=self.skill_tree.yview
                )
                self.skill_tree.configure(yscrollcommand=skill_scroll.set)
                self.skill_tree.grid(row=0, column=0, sticky="nsew")
                skill_scroll.grid(row=0, column=1, sticky="ns")
                self.skill_tree.bind(
                    "<<TreeviewSelect>>", self._skill_selection_changed
                )
                self.skill_tree.tag_configure("unlocked", foreground=COLORS["success"])
                self.skill_tree.tag_configure("locked", foreground=COLORS["muted"])

                actions = tk.Frame(page, bg=COLORS["panel"])
                actions.pack(fill="x", padx=28, pady=(12, 24))
                ttk.Button(
                    actions, text="LOCK SELECTED",
                    command=lambda: self._apply_selected_skill_rank(0),
                ).pack(side="left")
                ttk.Button(
                    actions, text="UNLOCK / SET RANK", style="Accent.TButton",
                    command=self._apply_selected_skill_rank,
                ).pack(side="left", padx=(10, 0))
                ttk.Button(
                    actions, text="MAX SELECTED",
                    command=self._max_selected_skills,
                ).pack(side="left", padx=(10, 0))
                ttk.Button(
                    actions, text="MAX VISIBLE TREE",
                    command=self._max_visible_skills,
                ).pack(side="right")
                continue
            if key == "progression":
                workspace = tk.Frame(page, bg=COLORS["panel"])
                workspace.pack(fill="both", expand=True, padx=28, pady=(20, 26))
                workspace.columnconfigure(0, weight=3)
                workspace.columnconfigure(1, weight=2)
                workspace.rowconfigure(0, weight=1)

                stats_panel = tk.Frame(
                    workspace, bg=COLORS["panel_alt"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                stats_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
                tk.Label(
                    stats_panel, text="PLAYER VALUES", bg=COLORS["red"],
                    fg="white", font=("Segoe UI Bold", 10),
                    anchor="w", padx=16, pady=12,
                ).pack(fill="x")
                form = tk.Frame(stats_panel, bg=COLORS["panel_alt"])
                form.pack(fill="both", expand=True, padx=20, pady=18)
                form.columnconfigure(1, weight=1)
                self.progression_vars = {
                    name: tk.StringVar(value="0")
                    for name in (
                        "health", "fury", "cash", "storage_cash",
                        "days_elapsed", "time_of_day",
                    )
                }
                progression_fields = [
                    (
                        "Current health / healing", "health",
                        "Temporary health; the game clamps this to calculated max health",
                    ),
                    ("Fury meter", "fury", "Stored rage/fury amount"),
                    ("Carried cash", "cash", "Money in player inventory"),
                    ("Stash cash", "storage_cash", "Money stored in player storage"),
                    ("Days elapsed", "days_elapsed", "World-day counter"),
                    ("Time of day", "time_of_day", "0.0–1.0 day-cycle position"),
                ]
                for row, (label, name, hint) in enumerate(progression_fields):
                    label_frame = tk.Frame(form, bg=COLORS["panel_alt"])
                    label_frame.grid(row=row, column=0, sticky="w", pady=8)
                    tk.Label(
                        label_frame, text=label, bg=COLORS["panel_alt"],
                        fg="white", font=("Segoe UI Semibold", 10), anchor="w",
                    ).pack(anchor="w")
                    tk.Label(
                        label_frame, text=hint, bg=COLORS["panel_alt"],
                        fg=COLORS["muted"], font=("Segoe UI", 8), anchor="w",
                    ).pack(anchor="w")
                    ttk.Entry(
                        form, textvariable=self.progression_vars[name],
                        justify="right",
                    ).grid(row=row, column=1, sticky="ew", padx=(20, 0), pady=8)
                buttons = tk.Frame(form, bg=COLORS["panel_alt"])
                buttons.grid(row=len(progression_fields), column=0, columnspan=2,
                             sticky="ew", pady=(18, 0))
                ttk.Button(
                    buttons, text="APPLY PLAYER VALUES", style="Accent.TButton",
                    command=self._apply_progression_values,
                ).pack(side="right")
                ttk.Button(
                    buttons, text="MAX MONEY",
                    command=self._max_progression_money,
                ).pack(side="right", padx=(0, 10))

                preset_panel = tk.Frame(
                    workspace, bg=COLORS["panel_alt"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                preset_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
                tk.Label(
                    preset_panel, text="PROGRESSION PRESETS", bg=COLORS["red_deep"],
                    fg="white", font=("Segoe UI Bold", 10),
                    anchor="w", padx=16, pady=12,
                ).pack(fill="x")
                preset_scroll_area = tk.Frame(
                    preset_panel, bg=COLORS["panel_alt"]
                )
                preset_scroll_area.pack(fill="both", expand=True)
                preset_canvas = tk.Canvas(
                    preset_scroll_area, bg=COLORS["panel_alt"],
                    highlightthickness=0, bd=0,
                )
                preset_scrollbar = ttk.Scrollbar(
                    preset_scroll_area, orient="vertical",
                    command=preset_canvas.yview,
                )
                preset_canvas.configure(yscrollcommand=preset_scrollbar.set)
                preset_canvas.pack(side="left", fill="both", expand=True)
                preset_scrollbar.pack(side="right", fill="y")
                preset_body = tk.Frame(preset_canvas, bg=COLORS["panel_alt"])
                preset_window = preset_canvas.create_window(
                    (0, 0), window=preset_body, anchor="nw"
                )
                preset_body.bind(
                    "<Configure>",
                    lambda _event, canvas=preset_canvas:
                        canvas.configure(scrollregion=canvas.bbox("all")),
                )
                preset_canvas.bind(
                    "<Configure>",
                    lambda event, canvas=preset_canvas, window_id=preset_window:
                        canvas.itemconfigure(window_id, width=event.width),
                )
                preset_canvas.bind(
                    "<MouseWheel>",
                    lambda event, canvas=preset_canvas:
                        canvas.yview_scroll(int(-event.delta / 120), "units"),
                )
                preset_body.configure(padx=18, pady=16)
                tk.Label(
                    preset_body,
                    text=(
                        "Safe presets max the skills belonging to each progression "
                        "tree. Exact XP counters are intentionally left untouched."
                    ),
                    bg=COLORS["panel_alt"], fg=COLORS["muted"],
                    font=("Segoe UI", 9), justify="left", wraplength=420,
                ).pack(fill="x", pady=(0, 14))
                for label, categories in (
                    ("MAX AGILITY / RUNNER", {"Runner", "Stamina_Auto"}),
                    ("MAX POWER / FIGHTER", {"Fighter"}),
                    ("MAX SURVIVOR / STATUS", {"Status", "Reputation"}),
                    ("MAX DRIVER", {"Driver"}),
                    ("MAX LEGEND", {"Legend", "Legend_Auto"}),
                    ("MAX ALL PROGRESSION", None),
                ):
                    ttk.Button(
                        preset_body, text=label,
                        style="Accent.TButton" if categories is None else "TButton",
                        command=lambda selected=categories:
                            self._apply_progression_preset(selected),
                    ).pack(fill="x", pady=5)
                ttk.Button(
                    preset_body, text="MAX HEALTH UPGRADES",
                    style="Accent.TButton",
                    command=self._max_health_upgrades,
                ).pack(fill="x", pady=5)
                ttk.Separator(preset_body).pack(fill="x", pady=14)
                time_buttons = tk.Frame(preset_body, bg=COLORS["panel_alt"])
                time_buttons.pack(fill="x")
                ttk.Button(
                    time_buttons, text="SET DAY",
                    command=lambda: self._set_progression_time(0.5),
                ).pack(side="left", expand=True, fill="x", padx=(0, 5))
                ttk.Button(
                    time_buttons, text="SET NIGHT",
                    command=lambda: self._set_progression_time(0.0),
                ).pack(side="left", expand=True, fill="x", padx=(5, 0))
                def bind_preset_wheel(widget: tk.Widget) -> None:
                    widget.bind(
                        "<MouseWheel>",
                        lambda event, canvas=preset_canvas:
                            canvas.yview_scroll(int(-event.delta / 120), "units"),
                    )
                    for child in widget.winfo_children():
                        bind_preset_wheel(child)
                bind_preset_wheel(preset_body)
                continue
            if key == "devtools":
                workspace = tk.Frame(page, bg=COLORS["panel"])
                workspace.pack(fill="both", expand=True, padx=28, pady=(20, 28))
                workspace.columnconfigure(0, weight=3)
                workspace.columnconfigure(1, weight=2)
                workspace.rowconfigure(0, weight=1)

                tools = tk.Frame(
                    workspace, bg=COLORS["panel_alt"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                tools.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
                tk.Label(
                    tools, text="SAVE TOOLKIT", bg=COLORS["red"], fg="white",
                    font=("Segoe UI Bold", 10), anchor="w", padx=16, pady=12,
                ).pack(fill="x")
                tk.Label(
                    tools,
                    text=(
                        "These operations modify data that genuinely exists in a "
                        "Dying Light save. Review the result, then use SAVE CHANGES."
                    ),
                    bg=COLORS["panel_alt"], fg=COLORS["muted"],
                    font=("Segoe UI", 9), justify="left", wraplength=650,
                ).pack(fill="x", padx=20, pady=(18, 12))
                actions = tk.Frame(tools, bg=COLORS["panel_alt"])
                actions.pack(fill="x", padx=20)
                actions.columnconfigure(0, weight=1)
                actions.columnconfigure(1, weight=1)
                developer_actions = (
                    ("VERIFIED ULTRA-DAMAGE SAVE PROFILE", self._dev_ultra_damage),
                    ("REVERT ULTRA DAMAGE", self._revert_ultra_damage),
                    ("REPAIR BROKEN WEAPON VALUES", self._dev_repair_weapons),
                    ("UNLOCK COLLECTIBLE OUTFITS", self._unlock_collectible_outfits),
                    ("MAX MONEY", self._dev_max_money),
                    ("MAX ALL SKILL TREES", lambda: self._apply_progression_preset(None)),
                    ("MAX HEALTH UPGRADES", self._max_health_upgrades),
                    ("SET DAY", lambda: self._dev_set_time(0.5, "day")),
                    ("SET NIGHT", lambda: self._dev_set_time(0.0, "night")),
                )
                for index, (label, command) in enumerate(developer_actions):
                    ttk.Button(
                        actions, text=label, command=command,
                        style="Accent.TButton" if index < 2 else "TButton",
                    ).grid(
                        row=index // 2, column=index % 2, sticky="ew",
                        padx=(0, 6) if index % 2 == 0 else (6, 0), pady=6,
                    )
                ttk.Separator(tools).pack(fill="x", padx=20, pady=18)
                ttk.Button(
                    tools, text="ADD COMPLETE ITEM CATALOGUE",
                    command=self.spawn_all_items, style="Accent.TButton",
                ).pack(fill="x", padx=20)
                tk.Label(
                    tools,
                    text="Large operation: adds missing source-catalogue records only.",
                    bg=COLORS["panel_alt"], fg=COLORS["muted"],
                    font=("Segoe UI", 8), anchor="w",
                ).pack(fill="x", padx=20, pady=(7, 18))

                runtime = tk.Frame(
                    workspace, bg=COLORS["panel_alt"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                runtime.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
                tk.Label(
                    runtime, text="IN-GAME ONLY", bg=COLORS["red_deep"], fg="white",
                    font=("Segoe UI Bold", 10), anchor="w", padx=16, pady=12,
                ).pack(fill="x")
                tk.Label(
                    runtime,
                    text=(
                        "The following menu options are runtime modifications, "
                        "not save fields:\n\n"
                        "  • God mode and damage immunity\n"
                        "  • Unlimited stamina and instant regeneration\n"
                        "  • No fall or explosion damage\n"
                        "  • Teleport, weather and mission controls\n"
                        "  • AI, physics and world debugging\n\n"
                        "They require an installed PAK mod and cannot be safely "
                        "embedded in a .sav editor."
                    ),
                    bg=COLORS["panel_alt"], fg="#e7e7ed",
                    font=("Segoe UI", 10), justify="left", anchor="nw",
                    wraplength=440, padx=22, pady=20,
                ).pack(fill="both", expand=True)
                continue
            if key == "runtime":
                self.runtime_game_var = tk.StringVar(
                    value=str(self._detect_dying_light_folder() or "")
                )
                self.runtime_status_var = tk.StringVar()
                workspace = tk.Frame(page, bg=COLORS["panel"])
                workspace.pack(fill="both", expand=True, padx=28, pady=(20, 28))

                location = tk.Frame(
                    workspace, bg=COLORS["panel_alt"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                location.pack(fill="x")
                tk.Label(
                    location, text="DYING LIGHT INSTALLATION", bg=COLORS["red_deep"],
                    fg="white", font=("Segoe UI Bold", 10),
                    anchor="w", padx=16, pady=12,
                ).pack(fill="x")
                path_row = tk.Frame(location, bg=COLORS["panel_alt"])
                path_row.pack(fill="x", padx=18, pady=16)
                path_row.columnconfigure(0, weight=1)
                ttk.Entry(
                    path_row, textvariable=self.runtime_game_var
                ).grid(row=0, column=0, sticky="ew")
                ttk.Button(
                    path_row, text="BROWSE", command=self._browse_runtime_game
                ).grid(row=0, column=1, padx=(10, 0))
                ttk.Button(
                    path_row, text="REFRESH STATUS",
                    command=self._refresh_runtime_status,
                ).grid(row=0, column=2, padx=(10, 0))

                cards = tk.Frame(workspace, bg=COLORS["panel"])
                cards.pack(fill="both", expand=True, pady=(16, 0))
                cards.columnconfigure(0, weight=1, uniform="runtime")
                cards.columnconfigure(1, weight=1, uniform="runtime")
                cards.rowconfigure(0, weight=1)
                runtime_cards = (
                    (
                        0, "DEV MENU + CUSTOM WEAPON DAMAGE",
                        "Adds the in-game pause-menu tools: cheats, item and storage "
                        "menus, locations, XP, missions, collectables, vehicle tools "
                        "and developer/debug pages. Inventory damage editing now uses "
                        "save-only Legend multipliers and does not require this package.",
                        self._install_developer_menu, self._disable_developer_menu,
                    ),
                    (
                        1, "GOD MODE + SURVIVAL RULES",
                        "Installs extreme health and stamina, instant regeneration, "
                        "no stamina drain, huge fall thresholds and reduced explosion "
                        "damage. Intended for The Following/DW_DLC1.",
                        self._install_godmode, self._disable_godmode,
                    ),
                )
                for column, heading, text, install, disable in runtime_cards:
                    card = tk.Frame(
                        cards, bg=COLORS["panel_alt"],
                        highlightbackground=COLORS["border"], highlightthickness=1,
                    )
                    card.grid(
                        row=0, column=column, sticky="nsew",
                        padx=(0, 8) if column == 0 else (8, 0),
                    )
                    tk.Label(
                        card, text=heading, bg=COLORS["red"], fg="white",
                        font=("Segoe UI Bold", 11), anchor="w", padx=16, pady=13,
                    ).pack(fill="x")
                    tk.Label(
                        card, text=text, bg=COLORS["panel_alt"], fg="#e7e7ed",
                        font=("Segoe UI", 10), justify="left", anchor="nw",
                        wraplength=540, padx=20, pady=20,
                    ).pack(fill="both", expand=True)
                    button_row = tk.Frame(card, bg=COLORS["panel_alt"])
                    button_row.pack(fill="x", padx=20, pady=(0, 20))
                    ttk.Button(
                        button_row, text="INSTALL / UPDATE", command=install,
                        style="Accent.TButton",
                    ).pack(side="left", expand=True, fill="x", padx=(0, 5))
                    ttk.Button(
                        button_row, text="DISABLE / RESTORE", command=disable,
                    ).pack(side="left", expand=True, fill="x", padx=(5, 0))
                tk.Label(
                    workspace, textvariable=self.runtime_status_var,
                    bg=COLORS["panel"], fg=COLORS["success"],
                    font=("Segoe UI Semibold", 9), anchor="w",
                ).pack(fill="x", pady=(14, 0))
                self.after_idle(self._refresh_runtime_status)
                continue
            if key == "cheatengine":
                self.ce_path_var = tk.StringVar(
                    value=str(self._detect_cheat_engine() or "")
                )
                self.ce_status_var = tk.StringVar()
                self.ce_name_var = tk.StringVar()
                self.ce_address_var = tk.StringVar()
                self.ce_type_var = tk.StringVar(value="4 Bytes")
                self.ce_entries: list[dict[str, str]] = []

                workspace = tk.Frame(page, bg=COLORS["panel"])
                workspace.pack(fill="both", expand=True, padx=28, pady=(20, 28))
                workspace.columnconfigure(0, weight=1)
                workspace.rowconfigure(3, weight=1)

                connection = tk.Frame(
                    workspace, bg=COLORS["panel_alt"],
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                connection.grid(row=0, column=0, sticky="ew")
                connection.columnconfigure(0, weight=1)
                tk.Label(
                    connection, text="CHEAT ENGINE CONNECTION",
                    bg=COLORS["red_deep"], fg="white",
                    font=("Segoe UI Bold", 10), anchor="w", padx=16, pady=12,
                ).grid(row=0, column=0, columnspan=4, sticky="ew")
                ttk.Entry(
                    connection, textvariable=self.ce_path_var
                ).grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=14)
                ttk.Button(
                    connection, text="BROWSE", command=self._browse_cheat_engine
                ).grid(row=1, column=1, padx=4)
                ttk.Button(
                    connection, text="GET CHEAT ENGINE",
                    command=lambda: webbrowser.open(
                        "https://www.cheatengine.org/downloads.php"
                    ),
                ).grid(row=1, column=2, padx=4)
                ttk.Button(
                    connection, text="REFRESH", command=self._refresh_ce_status
                ).grid(row=1, column=3, padx=(4, 16))
                tk.Label(
                    connection, textvariable=self.ce_status_var,
                    bg=COLORS["panel_alt"], fg=COLORS["success"],
                    font=("Segoe UI Semibold", 9), anchor="w",
                ).grid(
                    row=2, column=0, columnspan=4, sticky="ew",
                    padx=16, pady=(0, 12),
                )

                builtin = tk.Frame(
                    workspace, bg="#15151b",
                    highlightbackground="#5e1730", highlightthickness=1,
                )
                builtin.grid(row=1, column=0, sticky="ew", pady=(14, 0))
                builtin.columnconfigure(0, weight=1)
                tk.Label(
                    builtin, text="SYNSTERIC'S DL1 WORKSTATION 1.1.3",
                    bg="#15151b", fg="white",
                    font=("Segoe UI Bold", 11), anchor="w",
                ).grid(row=0, column=0, sticky="ew", padx=16, pady=(13, 3))
                tk.Label(
                    builtin,
                    text=(
                        "814 entries • Dying Light 1.53 • Player, inventory, "
                        "weapons, world, teleport, AI, buggy and debug tools"
                    ),
                    bg="#15151b", fg=COLORS["muted"],
                    font=("Segoe UI", 9), anchor="w",
                ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 13))
                ttk.Button(
                    builtin, text="LAUNCH BUILT-IN TABLE",
                    style="Accent.TButton", command=self._launch_builtin_ce_table,
                ).grid(row=0, column=1, rowspan=2, padx=16)

                form = tk.Frame(workspace, bg="#0c0c11")
                form.grid(row=2, column=0, sticky="ew", pady=(14, 10))
                form.columnconfigure(1, weight=2)
                form.columnconfigure(3, weight=3)
                tk.Label(
                    form, text="NAME", bg="#0c0c11", fg=COLORS["red"],
                    font=("Segoe UI Semibold", 8),
                ).grid(row=0, column=0, sticky="w", padx=(14, 6), pady=(10, 3))
                tk.Label(
                    form, text="ADDRESS / MODULE OFFSET",
                    bg="#0c0c11", fg=COLORS["red"],
                    font=("Segoe UI Semibold", 8),
                ).grid(row=0, column=2, sticky="w", padx=(14, 6), pady=(10, 3))
                tk.Label(
                    form, text="TYPE", bg="#0c0c11", fg=COLORS["red"],
                    font=("Segoe UI Semibold", 8),
                ).grid(row=0, column=4, sticky="w", padx=(14, 6), pady=(10, 3))
                ttk.Entry(form, textvariable=self.ce_name_var).grid(
                    row=1, column=0, columnspan=2, sticky="ew",
                    padx=(14, 6), pady=(0, 12),
                )
                ttk.Entry(form, textvariable=self.ce_address_var).grid(
                    row=1, column=2, columnspan=2, sticky="ew",
                    padx=(8, 6), pady=(0, 12),
                )
                ttk.Combobox(
                    form, textvariable=self.ce_type_var,
                    values=(
                        "Byte", "2 Bytes", "4 Bytes", "8 Bytes",
                        "Float", "Double", "String", "Array of byte",
                    ),
                    state="readonly", width=15,
                ).grid(row=1, column=4, padx=(8, 6), pady=(0, 12))
                ttk.Button(
                    form, text="ADD ENTRY", style="Accent.TButton",
                    command=self._add_ce_entry,
                ).grid(row=1, column=5, padx=(8, 14), pady=(0, 12))

                table = tk.Frame(workspace, bg=COLORS["panel_alt"])
                table.grid(row=3, column=0, sticky="nsew")
                table.columnconfigure(0, weight=1)
                table.rowconfigure(0, weight=1)
                self.ce_tree = ttk.Treeview(
                    table, columns=("name", "address", "type"),
                    show="headings", selectmode="extended",
                )
                for column, heading, width in (
                    ("name", "DESCRIPTION", 320),
                    ("address", "ADDRESS / POINTER", 520),
                    ("type", "VALUE TYPE", 160),
                ):
                    self.ce_tree.heading(column, text=heading)
                    self.ce_tree.column(column, width=width, anchor="w")
                ce_scroll = ttk.Scrollbar(
                    table, orient="vertical", command=self.ce_tree.yview
                )
                self.ce_tree.configure(yscrollcommand=ce_scroll.set)
                self.ce_tree.grid(row=0, column=0, sticky="nsew")
                ce_scroll.grid(row=0, column=1, sticky="ns")

                actions = tk.Frame(workspace, bg=COLORS["panel"])
                actions.grid(row=4, column=0, sticky="ew", pady=(12, 0))
                ttk.Button(
                    actions, text="REMOVE SELECTED",
                    command=self._remove_ce_entries,
                ).pack(side="left")
                ttk.Button(
                    actions, text="OPEN EXISTING .CT",
                    command=self._open_existing_ce_table,
                ).pack(side="left", padx=(8, 0))
                ttk.Button(
                    actions, text="EXPORT TABLE",
                    command=self._export_ce_table,
                ).pack(side="right", padx=(8, 0))
                ttk.Button(
                    actions, text="LAUNCH & ATTACH", style="Accent.TButton",
                    command=self._launch_cheat_engine,
                ).pack(side="right")
                tk.Label(
                    actions,
                    text=(
                        "Use stable pointers or AOB-backed symbols from a verified table. "
                        "Fixed addresses usually change after restarting the game."
                    ),
                    bg=COLORS["panel"], fg=COLORS["muted"],
                    font=("Segoe UI", 8), anchor="w",
                ).pack(side="left", padx=14)
                self.after_idle(self._refresh_ce_status)
                continue
            if key == "dashboard":
                cards = tk.Frame(page, bg=COLORS["panel"])
                cards.pack(fill="both", expand=True, padx=28, pady=(24, 28))
                for column in range(3):
                    cards.columnconfigure(column, weight=1, uniform="dashboard")
                for row in range(2):
                    cards.rowconfigure(row, weight=1, uniform="dashboard")
                self.dashboard_values: dict[str, tk.StringVar] = {}
                dashboard_cards = [
                    ("file", "SAVE FILE", "No save loaded", "SAV"),
                    ("records", "INVENTORY RECORDS", "0", "ITEMS"),
                    ("units", "TOTAL ITEM UNITS", "0", "QTY"),
                    ("skills", "UNLOCKED SKILLS", "0", "SKILL"),
                    ("decoded", "DECODED SIZE", "0 bytes", "DATA"),
                    ("integrity", "SAVE INTEGRITY", "Waiting", "SAFE"),
                ]
                for index, (name, title_text, default, icon) in enumerate(dashboard_cards):
                    card = tk.Frame(
                        cards, bg="#15151b",
                        highlightbackground="#33232a", highlightthickness=1,
                    )
                    card.grid(
                        row=index // 3, column=index % 3, sticky="nsew",
                        padx=(0 if index % 3 == 0 else 7, 0 if index % 3 == 2 else 7),
                        pady=(0 if index < 3 else 7, 7 if index < 3 else 0),
                    )
                    top = tk.Frame(card, bg="#15151b")
                    top.pack(fill="x", padx=18, pady=(17, 8))
                    tk.Label(
                        top, text=icon, bg=COLORS["red_deep"], fg="#ff9db4",
                        font=("Consolas", 8, "bold"), padx=8, pady=4,
                    ).pack(side="left")
                    tk.Label(
                        top, text=title_text, bg="#15151b", fg=COLORS["muted"],
                        font=("Segoe UI Semibold", 9),
                    ).pack(side="left", padx=(9, 0))
                    value = tk.StringVar(value=default)
                    self.dashboard_values[name] = value
                    tk.Label(
                        card, textvariable=value, bg="#15151b", fg="white",
                        font=("Segoe UI Semibold", 17), anchor="w",
                        wraplength=360, justify="left",
                    ).pack(fill="x", padx=18, pady=(4, 6))
                    subtext = (
                        "Gzip valid • Header valid • Backups enabled"
                        if name == "integrity" else "Loaded from the active save"
                    )
                    tk.Label(
                        card, text=subtext, bg="#15151b",
                        fg=COLORS["success"] if name == "integrity" else "#776f74",
                        font=("Segoe UI", 8), anchor="w",
                    ).pack(fill="x", padx=18, pady=(0, 16))
                continue
            if key == "inspector":
                inspector_panel = tk.Frame(
                    page, bg="#08050d",
                    highlightbackground=COLORS["border"], highlightthickness=1,
                )
                inspector_panel.pack(
                    fill="both", expand=True, padx=28, pady=(20, 26)
                )
                inspector_panel.columnconfigure(0, weight=1)
                inspector_panel.rowconfigure(1, weight=1)
                tools = tk.Frame(inspector_panel, bg="#0d0912")
                tools.grid(row=0, column=0, columnspan=2, sticky="ew")
                tk.Label(
                    tools, text="SERIALIZED SAVE STRUCTURE",
                    bg="#0d0912", fg=COLORS["muted"],
                    font=("Segoe UI Semibold", 9), padx=12, pady=10,
                ).pack(side="left")
                ttk.Button(
                    tools, text="EXPAND ROOT",
                    command=self._expand_inspector_root,
                ).pack(side="right", padx=(5, 10), pady=6)
                ttk.Button(
                    tools, text="COLLAPSE ALL",
                    command=self._collapse_inspector,
                ).pack(side="right", pady=6)
                self.inspector_tree = ttk.Treeview(
                    inspector_panel,
                    columns=("value", "type"),
                    show="tree headings",
                    selectmode="browse",
                )
                self.inspector_tree.heading("#0", text="KEY")
                self.inspector_tree.heading("value", text="VALUE")
                self.inspector_tree.heading("type", text="TYPE")
                self.inspector_tree.column("#0", width=520, minwidth=180, anchor="w")
                self.inspector_tree.column(
                    "value", width=650, minwidth=180, anchor="w"
                )
                self.inspector_tree.column(
                    "type", width=170, minwidth=100, anchor="w"
                )
                inspector_y = ttk.Scrollbar(
                    inspector_panel, orient="vertical",
                    command=self.inspector_tree.yview,
                )
                inspector_x = ttk.Scrollbar(
                    inspector_panel, orient="horizontal",
                    command=self.inspector_tree.xview,
                )
                self.inspector_tree.configure(
                    yscrollcommand=inspector_y.set,
                    xscrollcommand=inspector_x.set,
                )
                self.inspector_tree.grid(row=1, column=0, sticky="nsew")
                inspector_y.grid(row=1, column=1, sticky="ns")
                inspector_x.grid(row=2, column=0, sticky="ew")
                self.inspector_tree.bind(
                    "<<TreeviewOpen>>", self._inspector_node_opened
                )
                self._inspector_values: dict[str, object] = {}
                continue
            if key == "about":
                team = tk.Frame(page, bg=COLORS["panel"])
                team.pack(fill="both", expand=True, padx=28, pady=(24, 28))
                team.columnconfigure(0, weight=1, uniform="team")
                team.columnconfigure(1, weight=1, uniform="team")

                tk.Label(
                    team, text="THE PEOPLE BEHIND THE PROJECT",
                    bg=COLORS["panel"], fg="#d89cff",
                    font=("Segoe UI Semibold", 9), anchor="w",
                ).grid(
                    row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16)
                )

                creator_card = tk.Frame(
                    team, bg="#160820",
                    highlightbackground="#8f42bf", highlightthickness=1,
                )
                creator_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
                tk.Label(
                    creator_card, text="Creator", bg="#160820",
                    fg="#d89cff", font=("Segoe UI Semibold", 9), anchor="w",
                ).pack(fill="x", padx=20, pady=(18, 12))
                tk.Label(
                    creator_card, text="Ayden", bg="#160820",
                    fg="white", font=("Segoe UI Bold", 13), anchor="w",
                ).pack(fill="x", padx=20)
                creator_link = tk.Label(
                    creator_card, text="github.com/Drxxpy-Services",
                    bg="#160820", fg="#dca8ff", activeforeground="white",
                    cursor="hand2",
                    font=("Segoe UI Semibold", 9, "underline"), anchor="w",
                )
                creator_link.pack(fill="x", padx=20, pady=(10, 0))
                creator_link.bind(
                    "<Button-1>",
                    lambda _event: webbrowser.open(
                        "https://github.com/Drxxpy-Services"
                    ),
                )
                tk.Label(
                    creator_card,
                    text=(
                        "Creator of Dying Light // Save Architect and the person "
                        "behind its vision, design, direction, and testing."
                    ),
                    bg="#160820", fg="#d9d2df", font=("Segoe UI", 10),
                    justify="left", anchor="nw", wraplength=610,
                ).pack(fill="both", expand=True, padx=20, pady=(18, 22))

                developers_card = tk.Frame(
                    team, bg="#160820",
                    highlightbackground="#8f42bf", highlightthickness=1,
                )
                developers_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
                tk.Label(
                    developers_card, text="Lead Developers", bg="#160820",
                    fg="#d89cff", font=("Segoe UI Semibold", 9), anchor="w",
                ).pack(fill="x", padx=20, pady=(18, 12))
                tk.Label(
                    developers_card, text="CaptainStains\nPoncho\nUnknown",
                    bg="#160820", fg="white", font=("Segoe UI Bold", 12),
                    justify="left", anchor="w",
                ).pack(fill="x", padx=20)
                tk.Label(
                    developers_card,
                    text=(
                        "The friends who helped develop, improve, test, and "
                        "bring Dying Light // Save Architect to life."
                    ),
                    bg="#160820", fg="#d9d2df", font=("Segoe UI", 10),
                    justify="left", anchor="nw", wraplength=610,
                ).pack(fill="both", expand=True, padx=20, pady=(18, 22))

                social_card = tk.Frame(
                    team, bg="#160820",
                    highlightbackground="#8f42bf", highlightthickness=1,
                )
                social_card.grid(
                    row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0)
                )
                tk.Label(
                    social_card, text="Social Links", bg="#160820",
                    fg="#d89cff", font=("Segoe UI Semibold", 9), anchor="w",
                ).pack(fill="x", padx=20, pady=(16, 10))
                tk.Label(
                    social_card, text="Connect with the project",
                    bg="#160820", fg="white", font=("Segoe UI Bold", 12),
                    anchor="w",
                ).pack(fill="x", padx=20, pady=(0, 12))
                social_links = tk.Frame(social_card, bg="#160820")
                social_links.pack(fill="x", padx=20, pady=(0, 18))
                social_links.columnconfigure(0, weight=1)
                social_links.columnconfigure(1, weight=1)

                def add_social_link(
                    row: int, column: int, text: str, target: str
                ) -> None:
                    link = tk.Label(
                        social_links, text=text, bg="#160820",
                        fg="#dca8ff", activeforeground="white",
                        cursor="hand2",
                        font=("Segoe UI Semibold", 9, "underline"),
                        anchor="w",
                    )
                    link.grid(
                        row=row, column=column, sticky="ew",
                        padx=(0, 18), pady=6,
                    )
                    link.bind(
                        "<Button-1>",
                        lambda _event, url=target: webbrowser.open(url),
                    )

                add_social_link(
                    0, 0, "Discord  —  Join the community",
                    "https://discord.com/invite/Ckp6wzx974",
                )
                add_social_link(
                    1, 0, "TikTok  —  @captain_stains",
                    "https://www.tiktok.com/@captain_stains",
                )
                add_social_link(
                    2, 0, "YouTube  —  @Warp_Clock",
                    "https://www.youtube.com/@Warp_Clock",
                )
                add_social_link(
                    0, 1, "TikTok  —  @unknownbooster",
                    "https://www.tiktok.com/@unknownbooster",
                )
                add_social_link(
                    1, 1, "TikTok  —  @aydenjames369",
                    "https://www.tiktok.com/@aydenjames369",
                )
                tk.Label(
                    social_links, text="Twitch  —  Coming soon",
                    bg="#160820", fg="#bdb2c4",
                    font=("Segoe UI", 9), anchor="w",
                ).grid(
                    row=2, column=1, sticky="ew",
                    padx=(0, 18), pady=6,
                )
                continue
            body = tk.Text(
                page, bg=COLORS["panel_alt"], fg=COLORS["text"],
                insertbackground=COLORS["red"], relief="flat", bd=0,
                font=("Consolas", 10), padx=18, pady=16, height=12,
                wrap="word", state="disabled"
            )
            body.pack(fill="both", expand=True, padx=28, pady=24)
            self.info_bodies[key] = body

    def _build_spawner_page(self) -> None:
        page = tk.Frame(
            self.page_host, bg=COLORS["panel"],
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        self.pages["spawner"] = page
        page.columnconfigure(0, weight=1)
        page.rowconfigure(2, weight=1)

        tk.Label(
            page, text="SOURCE ITEM CATALOGUE", bg=COLORS["panel"],
            fg=COLORS["red"], font=("Segoe UI Black", 17), anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 6))
        tk.Label(
            page,
            text=(
                "Browse the complete game catalogue, inspect item metadata, and add "
                "verified inventory records directly to the active save."
            ),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9),
            anchor="w", justify="left"
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))

        table_frame = ttk.Frame(page, style="Panel.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=24)
        table_frame.columnconfigure(0, weight=3)
        table_frame.columnconfigure(2, weight=2)
        table_frame.rowconfigure(1, weight=1)
        filters = tk.Frame(
            table_frame, bg="#0c0c11",
            highlightbackground=COLORS["border"], highlightthickness=1,
        )
        filters.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        filters.columnconfigure(0, weight=3)
        filters.columnconfigure(1, weight=1)
        self.spawner_search_var = tk.StringVar()
        self.spawner_category_var = tk.StringVar(value="All categories")
        tk.Label(
            filters, text="SEARCH ITEMS", bg="#0c0c11", fg=COLORS["red"],
            font=("Segoe UI Semibold", 8), anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=(10, 3))
        tk.Label(
            filters, text="SEARCH CATEGORIES", bg="#0c0c11", fg=COLORS["red"],
            font=("Segoe UI Semibold", 8), anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(8, 14), pady=(10, 3))
        ttk.Entry(filters, textvariable=self.spawner_search_var).grid(
            row=1, column=0, sticky="ew", padx=(14, 8)
        )
        categories = ["All categories"] + sorted(
            {category.replace("CategoryType_", "") for _, category in self.item_catalog}
        )
        category_box = ttk.Combobox(
            filters, textvariable=self.spawner_category_var,
            values=categories, state="normal", width=24
        )
        category_box.grid(row=1, column=1, sticky="ew", padx=(8, 14))
        quick_filters = tk.Frame(filters, bg="#0c0c11")
        quick_filters.grid(
            row=2, column=0, columnspan=2, sticky="ew",
            padx=14, pady=(9, 11),
        )
        tk.Label(
            quick_filters, text="QUICK FILTERS", bg="#0c0c11",
            fg=COLORS["muted"], font=("Segoe UI Semibold", 8),
        ).pack(side="left", padx=(0, 8))
        for label, value in (
            ("ALL", "All categories"),
            ("MELEE", "Melee"),
            ("FIREARMS", "Firearm"),
            ("MATERIALS", "CraftComponent"),
            ("THROWABLES", "Throwable"),
            ("VALUABLES", "Valuable"),
        ):
            tk.Button(
                quick_filters, text=label,
                command=lambda selected=value: self.spawner_category_var.set(selected),
                bg="#211017", fg="#f2c9d3", activebackground=COLORS["red_dark"],
                activeforeground="white", relief="flat", bd=0,
                font=("Segoe UI Semibold", 8), padx=10, pady=4,
                cursor="hand2",
            ).pack(side="left", padx=(0, 6))
        self.spawner_search_var.trace_add(
            "write", lambda *_args: self._refresh_spawner_rows()
        )
        self.spawner_category_var.trace_add(
            "write", lambda *_args: self._refresh_spawner_rows()
        )
        category_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_spawner_rows())

        self.spawner_tree = ttk.Treeview(
            table_frame,
            columns=("id", "category", "status"),
            show="headings",
            selectmode="browse",
        )
        self.spawner_tree.heading("id", text="ITEM IDENTIFIER")
        self.spawner_tree.heading("category", text="CATEGORY")
        self.spawner_tree.heading("status", text="SPAWN SUPPORT")
        self.spawner_tree.column("id", width=390, anchor="w")
        self.spawner_tree.column("category", width=145, anchor="w")
        self.spawner_tree.column("status", width=105, anchor="center")
        spawner_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.spawner_tree.yview
        )
        self.spawner_tree.configure(yscrollcommand=spawner_scroll.set)
        self.spawner_tree.grid(row=1, column=0, sticky="nsew")
        spawner_scroll.grid(row=1, column=1, sticky="ns")
        self.spawner_tree.bind(
            "<<TreeviewSelect>>", lambda _event: self._show_selected_item_details()
        )
        self.spawner_tree.tag_configure("even", background="#111116")
        self.spawner_tree.tag_configure("odd", background="#16161c")

        detail_panel = tk.Frame(
            table_frame, bg=COLORS["panel_alt"],
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        detail_panel.grid(row=1, column=2, sticky="nsew", padx=(14, 0))
        tk.Label(
            detail_panel, text="ITEM INSPECTOR", bg=COLORS["red"],
            fg="white", font=("Segoe UI Bold", 10), anchor="w",
            padx=16, pady=12
        ).pack(fill="x")
        summary = tk.Frame(detail_panel, bg=COLORS["panel_alt"])
        summary.pack(fill="x", padx=16, pady=(15, 10))
        self.detail_name_var = tk.StringVar(value="No item selected")
        self.detail_category_var = tk.StringVar(value="CATEGORY  —")
        self.detail_support_var = tk.StringVar(value="SUPPORT  —")
        self.detail_source_var = tk.StringVar(value="SOURCE  —")
        self.detail_mode_var = tk.StringVar(
            value="Select an item to inspect its source-defined properties."
        )
        tk.Label(
            summary, textvariable=self.detail_name_var, bg=COLORS["panel_alt"],
            fg="white", font=("Segoe UI Semibold", 14), anchor="w",
            wraplength=560, justify="left",
        ).pack(fill="x")
        badges = tk.Frame(summary, bg=COLORS["panel_alt"])
        badges.pack(fill="x", pady=(10, 9))
        for variable in (
            self.detail_category_var, self.detail_support_var, self.detail_source_var
        ):
            tk.Label(
                badges, textvariable=variable, bg="#281018", fg="#ffb1c3",
                font=("Segoe UI Semibold", 8), padx=9, pady=5,
            ).pack(side="left", padx=(0, 6))
        tk.Label(
            summary, textvariable=self.detail_mode_var, bg=COLORS["panel_alt"],
            fg=COLORS["muted"], font=("Segoe UI", 9), anchor="w",
            justify="left", wraplength=590,
        ).pack(fill="x")
        tk.Label(
            detail_panel, text="SOURCE PROPERTIES", bg="#111116",
            fg=COLORS["red"], font=("Segoe UI Semibold", 9),
            anchor="w", padx=14, pady=8,
        ).pack(fill="x", padx=1)
        property_frame = tk.Frame(detail_panel, bg=COLORS["panel_alt"])
        property_frame.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        property_frame.columnconfigure(0, weight=1)
        property_frame.rowconfigure(0, weight=1)
        self.detail_property_tree = ttk.Treeview(
            property_frame, columns=("property", "value"),
            show="headings", selectmode="browse",
        )
        self.detail_property_tree.heading("property", text="PROPERTY")
        self.detail_property_tree.heading("value", text="VALUE")
        self.detail_property_tree.column("property", width=170, anchor="w")
        self.detail_property_tree.column("value", width=330, anchor="w")
        detail_scroll = ttk.Scrollbar(
            property_frame, orient="vertical",
            command=self.detail_property_tree.yview,
        )
        self.detail_property_tree.configure(yscrollcommand=detail_scroll.set)
        self.detail_property_tree.grid(row=0, column=0, sticky="nsew")
        detail_scroll.grid(row=0, column=1, sticky="ns")
        self.detail_property_tree.tag_configure("even", background="#111116")
        self.detail_property_tree.tag_configure("odd", background="#17171d")
        self.detail_property_tree.insert(
            "", "end", values=("Selection", "Choose an item from the catalogue")
        )

        actions = ttk.Frame(page, padding=(24, 14, 24, 20), style="Panel.TFrame")
        actions.grid(row=3, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        self.spawner_status_var = tk.StringVar(
            value=f"{len(self.item_catalog):,} source item definitions loaded"
        )
        ttk.Label(
            actions, textvariable=self.spawner_status_var, style="Panel.TLabel"
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(actions, text="Quantity", style="Panel.TLabel").grid(
            row=0, column=1, padx=(10, 6)
        )
        self.spawner_quantity_var = tk.StringVar(value="1")
        ttk.Entry(
            actions, textvariable=self.spawner_quantity_var,
            width=10, justify="right"
        ).grid(row=0, column=2)
        self.spawn_button = ttk.Button(
            actions, text="ADD TO INVENTORY", style="Accent.TButton",
            state="disabled",
            command=self.spawn_selected_item
        )
        self.spawn_button.grid(row=0, column=3, padx=(10, 0))
        ttk.Button(
            actions, text="ADD ALL ITEMS",
            command=self.spawn_all_items,
        ).grid(row=0, column=4, padx=(10, 0))
        self._refresh_spawner_rows()

    def _set_item_detail_text(self, text: str) -> None:
        if not hasattr(self, "detail_mode_var"):
            return
        self.detail_mode_var.set(text)

    def _show_selected_item_details(self) -> None:
        selection = self.spawner_tree.selection()
        if not selection:
            return
        values = self.spawner_tree.item(selection[0], "values")
        identifier, category, status = map(str, values)
        details = self.item_details.get(identifier, {})
        properties = details.get("properties", [])
        lines = [
            identifier,
            "─" * min(42, len(identifier)),
            f"Category : {category}",
            f"Support  : {status}",
            f"Source   : {details.get('source', 'catalogue index')}",
            "",
        ]
        if status == "EXISTING":
            lines.extend(
                [
                    "WRITE MODE",
                    "Quantity can be edited because this save already contains a "
                    "serialized record for the item.",
                    "",
                ]
            )
        elif status in {"VERIFIED", "REFERENCE"}:
            lines.extend(
                [
                    "WRITE MODE",
                    "A new stackable record can be created from game-generated metadata "
                    "captured in a reference save.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "UNIVERSAL WRITE MODE",
                    "The item will be created from the closest compatible record "
                    "archetype already present in this save.",
                    "",
                ]
            )
        lines.append("SOURCE PROPERTIES")
        if properties:
            for name, value in properties[:60]:
                lines.append(f"{name:<22} {value}")
            if len(properties) > 60:
                lines.append(f"… {len(properties) - 60} more properties")
        else:
            lines.append("No additional properties were declared in this block.")
        self._set_item_detail_text("\n".join(lines))
        self.detail_name_var.set(identifier)
        self.detail_category_var.set(f"CATEGORY  {category.upper()}")
        self.detail_support_var.set(f"SUPPORT  {status}")
        self.detail_source_var.set(
            f"SOURCE  {details.get('source', 'catalogue index')}"
        )
        if status == "EXISTING":
            self.detail_mode_var.set(
                "Existing inventory record. Quantity changes update the item "
                "already present in this save."
            )
        elif status in {"VERIFIED", "REFERENCE"}:
            self.detail_mode_var.set(
                "Verified spawn record recovered from game-generated metadata."
            )
        else:
            self.detail_mode_var.set(
                "Universal spawn record. The verified serializer will place this "
                "item in the correct inventory section."
            )
        self.detail_property_tree.delete(*self.detail_property_tree.get_children())
        if properties:
            for index, (name, value) in enumerate(properties[:100]):
                self.detail_property_tree.insert(
                    "", "end", values=(name, value),
                    tags=("even" if index % 2 == 0 else "odd",),
                )
        else:
            self.detail_property_tree.insert(
                "", "end",
                values=("Information", "No additional source properties declared"),
            )
        if status in {"EXISTING", "VERIFIED", "REFERENCE", "UNIVERSAL"}:
            self.spawn_button.configure(
                state="normal",
                text="SET QUANTITY" if status == "EXISTING" else "ADD TO INVENTORY",
            )
            self.spawner_status_var.set(
                f"READY  •  {identifier}  •  {status.lower()} record"
            )
        else:
            self.spawn_button.configure(state="disabled", text="METADATA REQUIRED")
            self.spawner_status_var.set(
                f"LOCKED  •  {identifier} has no serialized reference template"
            )

    def _refresh_spawner_rows(self) -> None:
        if not hasattr(self, "spawner_tree"):
            return
        query = self.spawner_search_var.get().strip().casefold()
        selected_category = self.spawner_category_var.get().strip()
        existing = {
            entry.identifier for entry in self.save.entries
        } if self.save else set()
        self.spawner_tree.delete(*self.spawner_tree.get_children())
        self.spawn_button.configure(state="disabled", text="SELECT AN ITEM")
        shown = 0
        for identifier, category in self.item_catalog:
            simple_category = category.replace("CategoryType_", "")
            if (
                selected_category
                and selected_category.casefold() != "all categories"
                and selected_category.casefold() not in simple_category.casefold()
            ):
                continue
            if query and query not in identifier.casefold() and query not in simple_category.casefold():
                continue
            if identifier in existing:
                status = "EXISTING"
            elif identifier in SPAWN_TEMPLATES:
                status = "VERIFIED"
            elif identifier in REFERENCE_SPAWN_TEMPLATES:
                status = "REFERENCE"
            else:
                status = "UNIVERSAL"
            self.spawner_tree.insert(
                "", "end", values=(identifier, simple_category, status),
                tags=("even" if shown % 2 == 0 else "odd",),
            )
            shown += 1
        self.spawner_status_var.set(
            f"{shown:,} shown  •  {len(self.item_catalog):,} source definitions"
        )

    def spawn_selected_item(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        selection = self.spawner_tree.selection()
        if not selection:
            messagebox.showerror(APP_TITLE, "Select an item first.", parent=self)
            return
        selected_values = self.spawner_tree.item(selection[0], "values")
        identifier = str(selected_values[0])
        status = str(selected_values[2])
        try:
            quantity = int(self.spawner_quantity_var.get())
            max_stack = self._source_max_stack(identifier)
            if max_stack is not None and quantity > max_stack:
                raise SaveFormatError(
                    f"{identifier} has a source-defined maximum stack of "
                    f"{max_stack:,}."
                )
            if status in {"EXISTING", "VERIFIED", "REFERENCE"}:
                self.save.spawn_supported_item(identifier, quantity)
            else:
                category = SOURCE_CATEGORY_INDEX.get(identifier, "")
                self.save.spawn_catalog_item(identifier, category, quantity)
        except (ValueError, SaveFormatError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self.quantity_vars.clear()
        self._show_entries()
        self._refresh_information_pages()
        self._refresh_spawner_rows()
        self.status_var.set(
            f"STAGED  •  {identifier} × {quantity}  •  Press SAVE CHANGES to write"
        )
        messagebox.showinfo(
            APP_TITLE,
            f"{identifier} × {quantity} has been staged.\n\n"
            "Press SAVE CHANGES to write it to the save and create a backup.",
            parent=self,
        )

    def spawn_all_items(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        if not messagebox.askyesno(
            APP_TITLE,
            "Add every missing game-source item to this save?\n\n"
            "This can create more than 1,000 records. A backup will be made when "
            "you click SAVE CHANGES.",
            parent=self,
        ):
            return
        try:
            quantity = int(self.spawner_quantity_var.get())
            added = self.save.spawn_all_catalog_items(quantity)
        except (ValueError, SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self.quantity_vars.clear()
        self._show_entries()
        self._refresh_information_pages()
        self._refresh_spawner_rows()
        self.status_var.set(
            f"STAGED  •  {added:,} catalogue items  •  Press SAVE CHANGES to write"
        )
        messagebox.showinfo(
            APP_TITLE,
            f"Added {added:,} missing catalogue items.\n\n"
            "Press SAVE CHANGES to write them and create a backup.",
            parent=self,
        )

    def _source_max_stack(self, identifier: str) -> int | None:
        details = self.item_details.get(identifier, {})
        for name, value in details.get("properties", []):
            if name == "MaxStackCount":
                try:
                    return int(str(value), 0)
                except ValueError:
                    return None
        return None

    def show_page(self, key: str) -> None:
        if key not in self.pages:
            return
        self.current_page = key
        for page in self.pages.values():
            page.grid_forget()
        self.pages[key].grid(row=0, column=0, sticky="nsew")
        titles = {
            "dashboard": "DASHBOARD",
            "inventory": "INVENTORY",
            "spawner": "ITEM SPAWNER",
            "skills": "SKILLS",
            "progression": "PLAYER PROGRESSION",
            "devtools": "DEVELOPER TOOLS",
            "runtime": "RUNTIME MODS",
            "cheatengine": "CHEAT ENGINE",
            "inspector": "SAVE INSPECTOR",
            "backups": "BACKUPS",
            "about": "ABOUT US",
        }
        self.page_title.configure(text=titles[key])
        for name, button in self.nav_buttons.items():
            active = name == key
            button.configure(
                bg=COLORS["red"] if active else "#09070b",
                fg="white" if active else "#d9dae1",
                activebackground="#ff3b70" if active else COLORS["red_deep"],
                font=("Segoe UI Bold", 10) if active else ("Segoe UI Semibold", 10),
            )
        inventory_controls = key == "inventory"
        if inventory_controls:
            self.search_entry.grid()
            self.max_button.grid()
            self.reset_button.grid()
        else:
            self.search_entry.grid_remove()
            self.max_button.grid_remove()
            self.reset_button.grid_remove()

    def _set_info_body(self, key: str, text: str) -> None:
        body = self.info_bodies[key]
        body.configure(state="normal")
        body.delete("1.0", "end")
        body.insert("1.0", text)
        body.configure(state="disabled")

    @staticmethod
    def _inspector_value_summary(value: object) -> tuple[str, str]:
        if isinstance(value, dict):
            return "{...}", f"dict ({len(value)})"
        if isinstance(value, list):
            return "[...]", f"list ({len(value)})"
        if value is None:
            return "null", "null"
        if isinstance(value, bool):
            return ("true" if value else "false"), "bool"
        if isinstance(value, str):
            display = value.replace("\r", "\\r").replace("\n", "\\n")
            if len(display) > 240:
                display = display[:237] + "..."
            return display, "str"
        if isinstance(value, int):
            return f"{value:,}", "int"
        if isinstance(value, float):
            return f"{value:g}", "float"
        return str(value), type(value).__name__

    def _insert_inspector_node(
        self, parent: str, key: object, value: object, open_node: bool = False
    ) -> str:
        display, type_name = self._inspector_value_summary(value)
        iid = self.inspector_tree.insert(
            parent, "end", text=str(key), values=(display, type_name),
            open=open_node,
        )
        self._inspector_values[iid] = value
        if isinstance(value, (dict, list)) and value:
            self.inspector_tree.insert(iid, "end", text="Loading…", tags=("placeholder",))
        return iid

    def _load_inspector_children(self, iid: str) -> None:
        value = self._inspector_values.get(iid)
        children = self.inspector_tree.get_children(iid)
        if not children:
            return
        if not all("placeholder" in self.inspector_tree.item(child, "tags")
                   for child in children):
            return
        self.inspector_tree.delete(*children)
        if isinstance(value, dict):
            entries = value.items()
        elif isinstance(value, list):
            entries = enumerate(value)
        else:
            return
        for key, child_value in entries:
            self._insert_inspector_node(iid, key, child_value)

    def _populate_inspector_tree(self, data: object) -> None:
        if not hasattr(self, "inspector_tree"):
            return
        self.inspector_tree.delete(*self.inspector_tree.get_children())
        self._inspector_values.clear()
        root = self._insert_inspector_node("", "{...}", data, open_node=True)
        self._load_inspector_children(root)

    def _inspector_node_opened(self, _event: tk.Event | None = None) -> None:
        iid = self.inspector_tree.focus()
        if iid:
            self._load_inspector_children(iid)

    def _collapse_inspector(self) -> None:
        if not hasattr(self, "inspector_tree"):
            return
        def close_children(parent: str) -> None:
            for child in self.inspector_tree.get_children(parent):
                close_children(child)
                self.inspector_tree.item(child, open=False)
        close_children("")

    def _expand_inspector_root(self) -> None:
        if not hasattr(self, "inspector_tree"):
            return
        roots = self.inspector_tree.get_children("")
        if roots:
            self.inspector_tree.item(roots[0], open=True)
            self._load_inspector_children(roots[0])

    def _refresh_skill_tree(self) -> None:
        if not hasattr(self, "skill_tree"):
            return
        query = self.skill_search_var.get().strip().casefold()
        selected_tree = self.skill_category_var.get()
        levels = getattr(self, "skill_levels", {})
        self.skill_tree.delete(*self.skill_tree.get_children())
        for skill in self.skill_catalog:
            identifier = str(skill["id"])
            category = str(skill["category"])
            if selected_tree != "All trees" and category != selected_tree:
                continue
            if query and query not in identifier.casefold() and query not in category.casefold():
                continue
            level = int(levels.get(identifier, 0))
            self.skill_tree.insert(
                "", "end",
                values=(
                    identifier, category, skill["tier"], level,
                    skill["max_level"], "UNLOCKED" if level else "LOCKED",
                ),
                tags=("unlocked" if level else "locked",),
            )

    def _skill_selection_changed(self, _event: tk.Event | None = None) -> None:
        selection = self.skill_tree.selection()
        if not selection:
            return
        values = self.skill_tree.item(selection[0], "values")
        current = int(values[3])
        maximum = int(values[4])
        self.skill_rank_var.set(str(current if current > 0 else min(1, maximum)))

    def _apply_skill_changes(self, changes: dict[str, int]) -> None:
        if not self.save or not changes:
            return
        try:
            self.save.update_skill_levels(changes)
            self.skill_levels = self.save.read_skill_levels()
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_skill_tree()
        self._refresh_progression_values()
        self._refresh_information_pages(refresh_skills=False)
        self.status_var.set(
            f"STAGED  •  {len(changes):,} skill changes  •  "
            "Press SAVE CHANGES to write"
        )

    def _apply_selected_skill_rank(self, forced_rank: int | None = None) -> None:
        selection = self.skill_tree.selection()
        if not selection:
            messagebox.showerror(APP_TITLE, "Select one or more skills.", parent=self)
            return
        try:
            requested = (
                int(forced_rank) if forced_rank is not None
                else int(self.skill_rank_var.get())
            )
        except ValueError:
            messagebox.showerror(APP_TITLE, "Rank must be a whole number.", parent=self)
            return
        changes: dict[str, int] = {}
        for row in selection:
            values = self.skill_tree.item(row, "values")
            maximum = int(values[4])
            if requested < 0 or requested > maximum:
                messagebox.showerror(
                    APP_TITLE,
                    f"{values[0]} supports ranks 0 to {maximum}.",
                    parent=self,
                )
                return
            changes[str(values[0])] = requested
        self._apply_skill_changes(changes)

    def _max_selected_skills(self) -> None:
        changes = {
            str(self.skill_tree.item(row, "values")[0]):
            int(self.skill_tree.item(row, "values")[4])
            for row in self.skill_tree.selection()
        }
        self._apply_skill_changes(changes)

    def _max_visible_skills(self) -> None:
        changes = {
            str(self.skill_tree.item(row, "values")[0]):
            int(self.skill_tree.item(row, "values")[4])
            for row in self.skill_tree.get_children()
        }
        if not changes:
            return
        if messagebox.askyesno(
            APP_TITLE,
            f"Unlock and max all {len(changes):,} currently visible skills?",
            parent=self,
        ):
            self._apply_skill_changes(changes)

    def _refresh_progression_values(self) -> None:
        if not self.save or not hasattr(self, "progression_vars"):
            return
        try:
            values = self.save.read_player_progression()
        except (SaveFormatError, OSError, json.JSONDecodeError):
            return
        for name, value in values.items():
            self.progression_vars[name].set(str(value))

    def _apply_progression_values(self) -> None:
        if not self.save:
            return
        try:
            values = {
                "health": float(self.progression_vars["health"].get()),
                "fury": float(self.progression_vars["fury"].get()),
                "cash": int(self.progression_vars["cash"].get()),
                "storage_cash": int(self.progression_vars["storage_cash"].get()),
                "days_elapsed": int(self.progression_vars["days_elapsed"].get()),
                "time_of_day": float(self.progression_vars["time_of_day"].get()),
            }
            if values["cash"] < 0 or values["storage_cash"] < 0:
                raise ValueError("Money values cannot be negative.")
            if not 0.0 <= values["time_of_day"] <= 1.0:
                raise ValueError("Time of day must be between 0.0 and 1.0.")
            self.save.update_player_progression(values)
        except (ValueError, SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_progression_values()
        self.status_var.set(
            "STAGED  •  player progression values  •  "
            "Press SAVE CHANGES to write"
        )

    def _max_progression_money(self) -> None:
        self.progression_vars["cash"].set("999999999")
        self.progression_vars["storage_cash"].set("999999999")

    def _set_progression_time(self, value: float) -> None:
        self.progression_vars["time_of_day"].set(str(value))

    def _unlock_collectible_outfits(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        identifiers = [
            f"ZZZZ_Collectable_CollectableOutfit_{number:02d}"
            for number in range(1, 13)
        ]
        if not messagebox.askyesno(
            APP_TITLE,
            "Add all 12 developer-menu collectible outfit records?\n\n"
            "The records will be staged until you click SAVE CHANGES.",
            parent=self,
        ):
            return
        try:
            added = self.save.spawn_named_inventory_items(identifiers)
        except (ValueError, SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self.quantity_vars.clear()
        self._show_entries()
        self._refresh_information_pages()
        self.status_var.set(
            f"STAGED  •  {added} collectible outfit records  •  "
            "Press SAVE CHANGES to write"
        )
        messagebox.showinfo(
            APP_TITLE,
            f"Staged {added} collectible outfit records.\n\n"
            "Press SAVE CHANGES to write them and create a backup.",
            parent=self,
        )

    def _dev_max_money(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        try:
            values = self.save.read_player_progression()
            values["cash"] = 999999999
            values["storage_cash"] = 999999999
            self.save.update_player_progression(values)
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_progression_values()
        self.status_var.set(
            "STAGED  •  maximum carried and stash cash  •  "
            "Press SAVE CHANGES to write"
        )

    def _dev_repair_weapons(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        if not messagebox.askyesno(
            APP_TITLE,
            "Restore the verified working power value on every recognized weapon?\n\n"
            "Use this to repair weapons affected by the old 500,000 save-field preset.",
            parent=self,
        ):
            return
        try:
            changed = self.save.repair_all_weapon_power_values()
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self.quantity_vars.clear()
        self._show_entries()
        self._refresh_information_pages()
        self.status_var.set(
            f"STAGED  •  repaired power values on {changed} weapons  •  "
            "Press SAVE CHANGES to write"
        )
        messagebox.showinfo(
            APP_TITLE,
            f"Staged repairs for {changed} weapons.\n\n"
            "Press SAVE CHANGES to write them and create a backup.",
            parent=self,
        )

    def _dev_ultra_damage(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        levels = {
            "LegendSkill_UnarmedDamage": 5000,
            "LegendSkill_OneHandedDamage": 5000,
            "LegendSkill_TwoHandedDamage": 5000,
            "LegendSkill_FirearmsDamage": 8000,
            "LegendSkill_BowDamage": 8000,
            "LegendSkill_ThrowingDamage": 8000,
        }
        if not messagebox.askyesno(
            APP_TITLE,
            "Apply the verified Ultra Damage save profile?\n\n"
            "Recovered from the supplied 2021 save:\n"
            "• Unarmed / one-handed / two-handed: rank 5,000\n"
            "• Firearms / bows / throwing: rank 8,000\n\n"
            "This is save-only and affects every weapon in each category.",
            parent=self,
        ):
            return
        try:
            current_levels = self.save.read_skill_levels()
            backup_levels = {
                identifier: int(current_levels.get(identifier, 0))
                for identifier in levels
            }
            self._ultra_profile_backup_file().write_text(
                json.dumps(backup_levels, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            self.save.update_skill_levels(levels)
            self.skill_levels = self.save.read_skill_levels()
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_skill_tree()
        self._refresh_information_pages(refresh_skills=False)
        self.status_var.set(
            "STAGED  •  verified Ultra Damage Legend ranks  •  "
            "Press SAVE CHANGES to write"
        )
        messagebox.showinfo(
            APP_TITLE,
            "The verified Ultra Damage ranks are staged.\n\n"
            "Press SAVE CHANGES to write them and create a backup.",
            parent=self,
        )

    @staticmethod
    def _ultra_profile_backup_file() -> Path:
        return Path(__file__).resolve().with_name("ultra_damage_original_ranks.json")

    def _revert_ultra_damage(self) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        identifiers = (
            "LegendSkill_UnarmedDamage",
            "LegendSkill_OneHandedDamage",
            "LegendSkill_TwoHandedDamage",
            "LegendSkill_FirearmsDamage",
            "LegendSkill_BowDamage",
            "LegendSkill_ThrowingDamage",
        )
        backup_file = self._ultra_profile_backup_file()
        restored_snapshot = False
        try:
            saved = json.loads(backup_file.read_text(encoding="utf-8"))
            levels = {
                identifier: max(0, min(32_767, int(saved.get(identifier, 25))))
                for identifier in identifiers
            }
            restored_snapshot = True
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            levels = {identifier: 25 for identifier in identifiers}
        description = (
            "the ranks saved immediately before Ultra Damage was applied"
            if restored_snapshot else "the normal rank 25 for all damage categories"
        )
        if not messagebox.askyesno(
            APP_TITLE,
            f"Revert the Ultra Damage profile and restore {description}?\n\n"
            "The change will remain staged until you press SAVE CHANGES.",
            parent=self,
        ):
            return
        try:
            self.save.update_skill_levels(levels)
            self.skill_levels = self.save.read_skill_levels()
            if restored_snapshot and backup_file.exists():
                backup_file.unlink()
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_skill_tree()
        self._refresh_information_pages(refresh_skills=False)
        self.status_var.set(
            "STAGED  •  Ultra Damage reverted  •  Press SAVE CHANGES to write"
        )
        messagebox.showinfo(
            APP_TITLE,
            f"Ultra Damage has been reverted to {description}.\n\n"
            "Press SAVE CHANGES to write the restored ranks.",
            parent=self,
        )

    def _dev_set_time(self, value: float, label: str) -> None:
        if not self.save:
            messagebox.showerror(APP_TITLE, "Open a save first.", parent=self)
            return
        try:
            values = self.save.read_player_progression()
            values["time_of_day"] = value
            self.save.update_player_progression(values)
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_progression_values()
        self.status_var.set(
            f"STAGED  •  world time set to {label}  •  "
            "Press SAVE CHANGES to write"
        )

    def _apply_progression_preset(self, categories: set[str] | None) -> None:
        selected = [
            skill for skill in self.skill_catalog
            if categories is None or str(skill["category"]) in categories
        ]
        if not selected:
            return
        label = "all progression trees" if categories is None else ", ".join(sorted(categories))
        if not messagebox.askyesno(
            APP_TITLE,
            f"Unlock and max {len(selected):,} skills for {label}?",
            parent=self,
        ):
            return
        changes = {
            str(skill["id"]): int(skill["max_level"]) for skill in selected
        }
        self._apply_skill_changes(changes)

    def _max_health_upgrades(self) -> None:
        if not self.save:
            return
        health_skills = {
            "Health1": 1,
            "Health2": 1,
            "Health3": 1,
            "LegendSkill_MaxHealth": 25,
        }
        if not messagebox.askyesno(
            APP_TITLE,
            "Unlock every normal health upgrade and set Legend Max Health to rank 25?\n\n"
            "This changes the calculated HUD maximum. The current-health value alone "
            "cannot raise the maximum.",
            parent=self,
        ):
            return
        try:
            self.save.update_skill_levels(health_skills)
            values = self.save.read_player_progression()
            values["health"] = 999999.0
            self.save.update_player_progression(values)
            self.skill_levels = self.save.read_skill_levels()
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self._refresh_skill_tree()
        self._refresh_progression_values()
        self._refresh_information_pages(refresh_skills=False)
        self.status_var.set(
            "STAGED  •  maximum-health upgrades enabled  •  "
            "Press SAVE CHANGES to write"
        )

    @staticmethod
    def _detect_dying_light_folder() -> Path | None:
        candidates = [
            Path(r"E:\SteamLibrary\steamapps\common\Dying Light"),
            Path(r"D:\steam app\steamapps\common\Dying Light"),
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\Dying Light"),
        ]
        library_files = [
            Path(r"D:\steam app\steamapps\libraryfolders.vdf"),
            Path(r"C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf"),
        ]
        for library_file in library_files:
            try:
                text = library_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for raw in re.findall(r'"path"\s+"([^"]+)"', text):
                candidates.append(
                    Path(raw.replace(r"\\", "\\")) /
                    "steamapps" / "common" / "Dying Light"
                )
        for candidate in candidates:
            if (candidate / "DW").is_dir() and (candidate / "DW_DLC1").is_dir():
                return candidate
        return None

    @staticmethod
    def _detect_cheat_engine() -> Path | None:
        roots = (
            Path(r"C:\Program Files"),
            Path(r"C:\Program Files (x86)"),
        )
        names = (
            "cheatengine-x86_64.exe", "cheatengine-x86_64-SSE4-AVX2.exe",
            "Cheat Engine.exe",
        )
        for root in roots:
            for version in ("Cheat Engine 7.6", "Cheat Engine 7.5", "Cheat Engine"):
                for name in names:
                    candidate = root / version / name
                    if candidate.is_file():
                        return candidate
        return None

    def _browse_cheat_engine(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select the Cheat Engine executable",
            filetypes=(("Executables", "*.exe"), ("All files", "*.*")),
        )
        if selected:
            self.ce_path_var.set(selected)
            self._refresh_ce_status()

    @staticmethod
    def _dying_light_process_running() -> bool:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq DyingLightGame.exe", "/NH"],
                capture_output=True, text=True, creationflags=0x08000000,
                timeout=5,
            )
            return "DyingLightGame.exe" in result.stdout
        except (OSError, subprocess.SubprocessError):
            return False

    def _refresh_ce_status(self) -> None:
        if not hasattr(self, "ce_status_var"):
            return
        ce = Path(self.ce_path_var.get().strip())
        ce_state = "READY" if ce.is_file() else "NOT INSTALLED / SELECT EXE"
        game_state = (
            "DYING LIGHT RUNNING"
            if self._dying_light_process_running() else "GAME NOT RUNNING"
        )
        self.ce_status_var.set(f"CHEAT ENGINE: {ce_state}   •   {game_state}")

    def _add_ce_entry(self) -> None:
        name = self.ce_name_var.get().strip()
        address = self.ce_address_var.get().strip()
        value_type = self.ce_type_var.get().strip()
        if not name or not address:
            messagebox.showerror(
                APP_TITLE, "Enter both a description and an address.", parent=self
            )
            return
        if len(address) > 300 or any(char in address for char in "\r\n<>"):
            messagebox.showerror(
                APP_TITLE, "The address expression is not valid.", parent=self
            )
            return
        entry = {"name": name, "address": address, "type": value_type}
        self.ce_entries.append(entry)
        self.ce_tree.insert("", "end", values=(name, address, value_type))
        self.ce_name_var.set("")
        self.ce_address_var.set("")

    def _remove_ce_entries(self) -> None:
        selected = list(self.ce_tree.selection())
        if not selected:
            return
        indices = sorted(
            (self.ce_tree.index(iid) for iid in selected), reverse=True
        )
        for index in indices:
            if 0 <= index < len(self.ce_entries):
                self.ce_entries.pop(index)
        self.ce_tree.delete(*selected)

    def _write_ce_table(self, path: Path) -> None:
        root = ET.Element("CheatTable", CheatEngineTableVersion="45")
        entries = ET.SubElement(root, "CheatEntries")
        for index, item in enumerate(self.ce_entries):
            entry = ET.SubElement(entries, "CheatEntry")
            ET.SubElement(entry, "ID").text = str(index)
            ET.SubElement(entry, "Description").text = f'"{item["name"]}"'
            ET.SubElement(entry, "VariableType").text = item["type"]
            ET.SubElement(entry, "Address").text = item["address"]
        ET.SubElement(root, "UserdefinedSymbols")
        ET.SubElement(root, "LuaScript").text = (
            'local pid = getProcessIDFromProcessName("DyingLightGame.exe")\n'
            "if pid ~= nil and pid ~= 0 then\n"
            "  openProcess(pid)\n"
            "else\n"
            '  showMessage("Start Dying Light, then reopen or attach this table.")\n'
            "end\n"
        )
        ET.indent(root, space="  ")
        ET.ElementTree(root).write(
            path, encoding="utf-8", xml_declaration=True
        )

    def _export_ce_table(self) -> Path | None:
        selected = filedialog.asksaveasfilename(
            title="Export Cheat Engine table",
            defaultextension=".CT",
            initialfile="DyingLight_SaveArchitect.CT",
            filetypes=(("Cheat Engine tables", "*.CT"),),
        )
        if not selected:
            return None
        try:
            path = Path(selected)
            self._write_ce_table(path)
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not export table:\n{exc}", parent=self)
            return None
        self.status_var.set(f"CHEAT TABLE EXPORTED  •  {path.name}")
        return path

    def _launch_cheat_engine(self) -> None:
        ce = Path(self.ce_path_var.get().strip())
        if not ce.is_file():
            messagebox.showerror(
                APP_TITLE,
                "Cheat Engine was not found. Install it or select its executable.",
                parent=self,
            )
            return
        table = Path(__file__).resolve().with_name("DyingLight_SaveArchitect.CT")
        try:
            self._write_ce_table(table)
            subprocess.Popen(
                [str(ce), str(table)],
                cwd=str(ce.parent),
                creationflags=0x08000000,
            )
        except OSError as exc:
            messagebox.showerror(
                APP_TITLE, f"Could not launch Cheat Engine:\n{exc}", parent=self
            )
            return
        self.status_var.set(
            "CHEAT ENGINE LAUNCHED  •  table will attach to DyingLightGame.exe"
        )

    @staticmethod
    def _builtin_ce_table() -> Path:
        return (
            Path(__file__).resolve().with_name("cheat_tables")
            / "Synsteric_DL1_Workstation_1.1.3.CT"
        )

    def _launch_builtin_ce_table(self) -> None:
        ce = Path(self.ce_path_var.get().strip())
        table = self._builtin_ce_table()
        if not ce.is_file():
            messagebox.showerror(
                APP_TITLE,
                "Cheat Engine was not found. Install it or select its executable.",
                parent=self,
            )
            return
        if not table.is_file():
            messagebox.showerror(
                APP_TITLE,
                f"The built-in cheat table is missing:\n{table}",
                parent=self,
            )
            return
        try:
            subprocess.Popen(
                [str(ce), str(table)], cwd=str(ce.parent),
                creationflags=0x08000000,
            )
        except OSError as exc:
            messagebox.showerror(
                APP_TITLE, f"Could not launch the built-in table:\n{exc}", parent=self
            )
            return
        self.status_var.set(
            "CHEAT ENGINE LAUNCHED  •  Synsteric DL1 Workstation 1.1.3"
        )

    def _open_existing_ce_table(self) -> None:
        ce = Path(self.ce_path_var.get().strip())
        if not ce.is_file():
            messagebox.showerror(
                APP_TITLE,
                "Cheat Engine was not found. Install it or select its executable.",
                parent=self,
            )
            return
        selected = filedialog.askopenfilename(
            title="Open an existing Cheat Engine table",
            filetypes=(("Cheat Engine tables", "*.CT"), ("All files", "*.*")),
        )
        if not selected:
            return
        try:
            subprocess.Popen(
                [str(ce), selected], cwd=str(ce.parent),
                creationflags=0x08000000,
            )
        except OSError as exc:
            messagebox.showerror(
                APP_TITLE, f"Could not launch Cheat Engine:\n{exc}", parent=self
            )

    def _runtime_game_folder(self) -> Path:
        folder = Path(self.runtime_game_var.get().strip())
        if not (folder / "DW").is_dir() or not (folder / "DW_DLC1").is_dir():
            raise SaveFormatError(
                "Select the Dying Light installation folder containing DW and DW_DLC1."
            )
        return folder

    def _browse_runtime_game(self) -> None:
        selected = filedialog.askdirectory(
            title="Select the Dying Light installation folder",
            initialdir=self.runtime_game_var.get() or str(Path.home()),
        )
        if selected:
            self.runtime_game_var.set(selected)
            self._refresh_runtime_status()

    @staticmethod
    def _runtime_asset(name: str) -> Path:
        return Path(__file__).resolve().with_name("runtime_mods") / name

    @staticmethod
    def _weapon_override_file() -> Path:
        return Path(__file__).resolve().with_name("weapon_damage_overrides.json")

    def _load_weapon_damage_overrides(self) -> dict[str, float]:
        try:
            data = json.loads(
                self._weapon_override_file().read_text(encoding="utf-8")
            )
            return {
                str(name): float(value) for name, value in data.items()
                if 1 <= float(value) <= 1_000_000
            }
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {}

    def _source_weapon_damage(self, identifier: str) -> float:
        properties = self.item_details.get(identifier, {}).get("properties", [])
        for wanted in ("FirePointDamage", "Damage"):
            for name, value in properties:
                if name != wanted:
                    continue
                match = re.search(r"(-?\d+(?:\.\d+)?)\s*$", str(value))
                if match:
                    return float(match.group(1))
        return 1.0

    @staticmethod
    def _rewrite_weapon_definition(
        text: str, identifier: str, damage: float
    ) -> tuple[str, int]:
        pattern = re.compile(
            r'Item\("' + re.escape(identifier) +
            r'",\s*CategoryType_[A-Za-z0-9_]+\)\s*\{'
        )
        replacements: list[tuple[int, int, str]] = []
        changed = 0
        for match in pattern.finditer(text):
            brace = text.find("{", match.start())
            depth = 0
            end = brace
            while end < len(text):
                if text[end] == "{":
                    depth += 1
                elif text[end] == "}":
                    depth -= 1
                    if depth == 0:
                        end += 1
                        break
                end += 1
            block = text[match.start():end]
            updated = re.sub(
                r"(?m)^(\s*)Damage\([^;\r\n]*\);",
                rf"\g<1>Damage({damage:g});",
                block,
            )
            updated = re.sub(
                r"(?m)^(\s*)FirePointDamage\(\s*([0-9]+)\s*,[^;\r\n]*\);",
                rf"\g<1>FirePointDamage(\g<2>,{damage:g});",
                updated,
            )
            if updated != block:
                replacements.append((match.start(), end, updated))
                changed += 1
        for start, end, replacement in reversed(replacements):
            text = text[:start] + replacement + text[end:]
        return text, changed

    def _build_custom_weapon_pak(
        self, overrides: dict[str, float]
    ) -> tuple[Path, int]:
        template = self._runtime_asset("SaveArchitect_RuntimeTemplate.pak")
        output = self._runtime_asset("SaveArchitect_CustomWeapons.pak")
        if not template.is_file():
            raise SaveFormatError(
                "The per-weapon runtime template is missing from runtime_mods."
            )
        changed_blocks = 0
        with zipfile.ZipFile(template, "r") as source, zipfile.ZipFile(
            output, "w", zipfile.ZIP_DEFLATED
        ) as target:
            for info in source.infolist():
                payload = source.read(info.filename)
                if (
                    info.filename.casefold().endswith(".scr")
                    and "/scripts/inventory/" in info.filename.casefold()
                ):
                    text = payload.decode("utf-8", errors="ignore")
                    for identifier, damage in overrides.items():
                        text, changed = self._rewrite_weapon_definition(
                            text, identifier, damage
                        )
                        changed_blocks += changed
                    payload = text.encode("utf-8")
                target.writestr(info.filename, payload)
        if not changed_blocks:
            output.unlink(missing_ok=True)
            raise SaveFormatError(
                "No matching weapon definition was found for this item."
            )
        return output, changed_blocks

    def _set_weapon_damage_override(
        self, identifier: str, damage: float, parent: tk.Widget
    ) -> None:
        if not self.save:
            raise SaveFormatError("Open a save before editing weapon damage.")
        overrides = self._load_weapon_damage_overrides()
        overrides[identifier] = damage
        self._weapon_override_file().write_text(
            json.dumps(overrides, indent=2, sort_keys=True), encoding="utf-8"
        )
        category = SOURCE_CATEGORY_INDEX.get(identifier, "")
        properties = self.item_details.get(identifier, {}).get("properties", [])
        two_handed = any(
            name == "TwoHanded" and str(value).strip().casefold() == "true"
            for name, value in properties
        )
        if category == "CategoryType_Firearm":
            skill, per_rank, generation_scale = (
                "LegendSkill_FirearmsDamage", 0.10, 2.40
            )
        elif category in {"CategoryType_Bow", "CategoryType_Crossbow"}:
            skill, per_rank, generation_scale = (
                "LegendSkill_BowDamage", 0.40, 1.0
            )
        elif category == "CategoryType_Melee":
            skill = (
                "LegendSkill_TwoHandedDamage"
                if two_handed else "LegendSkill_OneHandedDamage"
            )
            per_rank = 0.04
            generation_scale = 1.0
        else:
            raise SaveFormatError(
                "This weapon category has no verified save-only damage skill."
            )
        base_damage = max(1.0, self._source_weapon_damage(identifier))
        required_rank = max(
            0, min(
                32_767,
                int(
                    ((damage / (base_damage * generation_scale)) - 1.0)
                    / per_rank + 0.999999
                ),
            )
        )
        self.save.update_skill_levels({skill: required_rank})
        self.skill_levels = self.save.read_skill_levels()

    def _install_runtime_file(
        self, asset_name: str, relative_target: Path, display_name: str
    ) -> None:
        try:
            game = self._runtime_game_folder()
            asset = self._runtime_asset(asset_name)
            if not asset.is_file():
                raise SaveFormatError(
                    f"The packaged {display_name} file is missing:\n{asset}"
                )
            target = game / relative_target
            backup = target.with_name(target.name + ".save_architect_backup")
            created = target.with_name(target.name + ".save_architect_created")
            if not messagebox.askyesno(
                APP_TITLE,
                f"Install {display_name}?\n\n"
                "Close Dying Light before continuing. Any original target file will "
                "be backed up automatically.",
                parent=self,
            ):
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not backup.exists() and not created.exists():
                shutil.copy2(target, backup)
            elif not target.exists() and not backup.exists():
                created.write_text(
                    "Created by Dying Light Save Architect", encoding="utf-8"
                )
            shutil.copy2(asset, target)
        except (OSError, SaveFormatError) as exc:
            messagebox.showerror(
                APP_TITLE,
                f"Could not install {display_name}:\n\n{exc}\n\n"
                "Close the game and run the editor with permission to modify its "
                "installation folder.",
                parent=self,
            )
            return
        self._refresh_runtime_status()
        messagebox.showinfo(
            APP_TITLE,
            f"{display_name} installed successfully.\n\nLaunch Dying Light and "
            "open the pause menu to use the available developer controls.",
            parent=self,
        )

    def _disable_runtime_file(
        self, relative_target: Path, display_name: str
    ) -> None:
        try:
            game = self._runtime_game_folder()
            target = game / relative_target
            backup = target.with_name(target.name + ".save_architect_backup")
            created = target.with_name(target.name + ".save_architect_created")
            if not messagebox.askyesno(
                APP_TITLE,
                f"Disable {display_name} and restore the previous game file?",
                parent=self,
            ):
                return
            if backup.exists():
                shutil.copy2(backup, target)
                backup.unlink()
                if created.exists():
                    created.unlink()
            elif created.exists():
                if target.exists():
                    target.unlink()
                created.unlink()
            else:
                raise SaveFormatError(
                    "No Save Architect backup or installation marker was found. "
                    "The file was left untouched."
                )
        except (OSError, SaveFormatError) as exc:
            messagebox.showerror(
                APP_TITLE, f"Could not restore {display_name}:\n\n{exc}", parent=self
            )
            return
        self._refresh_runtime_status()
        messagebox.showinfo(
            APP_TITLE, f"{display_name} has been disabled.", parent=self
        )

    def _install_developer_menu(self) -> None:
        asset_name = (
            "SaveArchitect_CustomWeapons.pak"
            if self._runtime_asset("SaveArchitect_CustomWeapons.pak").is_file()
            else "SaveArchitect_RuntimeTemplate.pak"
        )
        self._install_runtime_file(
            asset_name, Path("DW") / "Data3.pak",
            "Developer Menu + Custom Weapon Damage",
        )

    def _disable_developer_menu(self) -> None:
        self._disable_runtime_file(
            Path("DW") / "Data3.pak", "Selvenik Developer Menu"
        )

    def _install_godmode(self) -> None:
        self._install_runtime_file(
            "Godmode_DataEn.pak", Path("DW_DLC1") / "DataEn.pak",
            "God Mode + Survival Rules",
        )

    def _disable_godmode(self) -> None:
        self._disable_runtime_file(
            Path("DW_DLC1") / "DataEn.pak", "God Mode + Survival Rules"
        )

    def _refresh_runtime_status(self) -> None:
        if not hasattr(self, "runtime_status_var"):
            return
        try:
            game = self._runtime_game_folder()
        except SaveFormatError:
            self.runtime_status_var.set("INSTALLATION NOT FOUND")
            return
        custom_weapon_asset = (
            "SaveArchitect_CustomWeapons.pak"
            if self._runtime_asset("SaveArchitect_CustomWeapons.pak").is_file()
            else "SaveArchitect_RuntimeTemplate.pak"
        )
        checks = (
            (
                "Dev menu + weapon overrides", game / "DW" / "Data3.pak",
                custom_weapon_asset,
            ),
            (
                "God mode", game / "DW_DLC1" / "DataEn.pak",
                "Godmode_DataEn.pak",
            ),
        )
        statuses = []
        for label, target, asset_name in checks:
            asset = self._runtime_asset(asset_name)
            installed = False
            try:
                installed = (
                    target.is_file() and asset.is_file()
                    and hashlib.sha256(target.read_bytes()).digest()
                    == hashlib.sha256(asset.read_bytes()).digest()
                )
            except OSError:
                pass
            statuses.append(f"{label}: {'INSTALLED' if installed else 'NOT INSTALLED'}")
        self.runtime_status_var.set("   •   ".join(statuses))

    def choose_save(self) -> None:
        if getattr(self, "_saving", False):
            return
        initial = DEFAULT_SAVE.parent if DEFAULT_SAVE.parent.exists() else Path.home()
        selected = filedialog.askopenfilename(
            title="Open Dying Light save",
            initialdir=initial,
            filetypes=[("Dying Light saves", "*.sav"), ("All files", "*.*")],
        )
        if selected:
            self.open_save(Path(selected))

    def reload_save(self) -> None:
        if getattr(self, "_saving", False):
            return
        if self.save:
            self.open_save(self.save.path)

    def open_save(self, path: Path) -> None:
        try:
            loaded = DyingLightSave.load(path)
        except SaveFormatError as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return
        self.save = loaded
        self.quantity_vars.clear()
        self.path_var.set(str(path))
        self._show_entries()
        self.status_var.set(
            f"READY  •  {len(loaded.entries)} inventory records  •  "
            f"{len(loaded.skills)} unlocked skills detected  •  "
            f"{len(loaded.decoded):,} decoded bytes"
        )
        self.save_button.configure(state="normal")
        self._refresh_information_pages()
        self._refresh_spawner_rows()
        self.show_page("dashboard")

    def _refresh_information_pages(self, refresh_skills: bool = True) -> None:
        if not self.save:
            return
        raw = self.save.path.read_bytes()
        item_total = sum(entry.quantity for entry in self.save.entries)
        if refresh_skills:
            try:
                self.skill_levels = self.save.read_skill_levels()
            except (SaveFormatError, OSError, json.JSONDecodeError):
                self.skill_levels = {
                    identifier: 1 for identifier in self.save.skills
                }
        self._refresh_skill_tree()
        self.dashboard_values["file"].set(self.save.path.name)
        self.dashboard_values["records"].set(f"{len(self.save.entries):,}")
        self.dashboard_values["units"].set(f"{item_total:,}")
        self.dashboard_values["skills"].set(f"{len(self.save.skills):,}")
        self.dashboard_values["decoded"].set(f"{len(self.save.decoded):,} bytes")
        self.dashboard_values["integrity"].set("VALID & PROTECTED")
        skills = "\n".join(f"  ◆ {skill}" for skill in self.save.skills)
        if not skills:
            skills = "  No serialized skill records detected in this early save."
        progression = (
            "Detected progression categories:\n\n"
            "  Runner / Agility\n  Fighter / Power\n  Status / Survivor\n"
            "  Reputation\n  Legend\n  Driver\n  Hellraid\n\n"
            "Editing is intentionally locked until controlled before/after samples "
            "confirm the XP, level and available-point fields."
        )
        try:
            inspector_data = self.save.read_inspector_data()
        except (SaveFormatError, OSError, json.JSONDecodeError):
            inspector_data = {
                "header": {
                    "file": self.save.path.name,
                    "containerSize": len(raw),
                    "decodedSize": len(self.save.decoded),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                },
                "inventory": [
                    {"identifier": entry.identifier, "quantity": entry.quantity}
                    for entry in self.save.entries
                ],
                "skills": list(self.save.skills),
            }
        self._populate_inspector_tree(inspector_data)
        backup_dir = self.save.path.parent / "DLSE Backups"
        backups = (
            sorted(backup_dir.glob("*.bak"), key=lambda item: item.stat().st_mtime, reverse=True)
            if backup_dir.exists()
            else []
        )
        backup_text = (
            "\n".join(
                f"  {backup.name}  •  {backup.stat().st_size:,} bytes"
                for backup in backups[:50]
            )
            or "  No editor backups have been created yet."
        )
        self._set_info_body("backups", backup_text)

    def _show_entries(self) -> None:
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.items_frame.columnconfigure(0, weight=1)

        header = tk.Frame(self.items_frame, bg="#0c0c11", height=72)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.columnconfigure(0, weight=5)
        header.columnconfigure(1, weight=2)
        header.columnconfigure(2, minsize=130)
        header.columnconfigure(3, minsize=150)
        for column, text, anchor in (
            (0, "ITEM DETAILS", "w"),
            (2, "QUANTITY", "e"),
            (3, "ACTIONS", "e"),
        ):
            tk.Label(
                header, text=text, bg="#0c0c11", fg=COLORS["red"],
                font=("Segoe UI Semibold", 9), anchor=anchor,
                padx=16,
            ).grid(row=0, column=column, rowspan=2, sticky="nsew")
        tk.Label(
            header, text="CATEGORY", bg="#0c0c11", fg=COLORS["red"],
            font=("Segoe UI Semibold", 9), anchor="w", padx=16,
        ).grid(row=0, column=1, sticky="ew")
        category_filter = ttk.Combobox(
            header,
            textvariable=self.inventory_category_var,
            values=["All categories", *self.inventory_categories],
            state="readonly",
            width=20,
        )
        category_filter.grid(
            row=1, column=1, sticky="w", padx=(16, 12), pady=(0, 8)
        )
        category_filter.bind(
            "<<ComboboxSelected>>", lambda _event: self._show_entries()
        )

        if not self.save:
            return
        validator = (self.register(self._validate_quantity), "%P")
        query = self.search_var.get().strip().casefold()
        selected_category = self.inventory_category_var.get()
        visible = [
            entry
            for entry in self.save.entries
            if (
                selected_category == "All categories"
                or SOURCE_CATEGORY_INDEX.get(
                    entry.identifier, "CategoryType_Inventory"
                ).replace("CategoryType_", "") == selected_category
            )
            and (
                not query
                or query in entry.display_name.casefold()
                or query in entry.identifier.casefold()
                or query in SOURCE_CATEGORY_INDEX.get(
                    entry.identifier, "CategoryType_Inventory"
                ).replace("CategoryType_", "").casefold()
            )
        ]
        for row, entry in enumerate(visible, start=1):
            row_color = "#111116" if row % 2 else "#15151b"
            card = tk.Frame(
                self.items_frame, bg=row_color,
                highlightbackground="#30262b", highlightthickness=0,
            )
            card.grid(row=row, column=0, sticky="ew", pady=(0, 1))
            card.columnconfigure(0, weight=5)
            card.columnconfigure(1, weight=2)
            card.columnconfigure(2, minsize=130)
            card.columnconfigure(3, minsize=150)

            details = tk.Frame(card, bg=row_color)
            details.grid(row=0, column=0, sticky="nsew", padx=16, pady=10)
            tk.Label(
                details, text=entry.display_name, bg=row_color, fg="#f7f3f5",
                font=("Segoe UI Semibold", 10), anchor="w",
            ).pack(fill="x")
            tk.Label(
                details, text=entry.identifier, bg=row_color, fg="#8f858b",
                font=("Consolas", 8), anchor="w",
            ).pack(fill="x", pady=(2, 0))

            category = SOURCE_CATEGORY_INDEX.get(
                entry.identifier, "CategoryType_Inventory"
            ).replace("CategoryType_", "")
            badge = tk.Label(
                card, text=category.upper(), bg="#281018", fg="#ff9bb2",
                font=("Segoe UI Semibold", 8), padx=10, pady=5,
            )
            badge.grid(row=0, column=1, sticky="w", padx=(4, 12))

            if entry.identifier not in self.quantity_vars:
                self.quantity_vars[entry.identifier] = tk.StringVar(value=str(entry.quantity))
            var = self.quantity_vars[entry.identifier]
            quantity_entry = tk.Entry(
                card,
                textvariable=var,
                width=10,
                justify="right",
                validate="key",
                validatecommand=validator,
                bg="#19191f", fg="white", insertbackground=COLORS["red"],
                relief="flat", highlightthickness=1,
                highlightbackground="#51434a", highlightcolor=COLORS["red"],
                font=("Consolas", 10),
            )
            quantity_entry.grid(
                row=0, column=2, sticky="e", padx=14, ipadx=8, ipady=7
            )
            tk.Button(
                card,
                text="EDIT VALUES",
                command=lambda name=entry.identifier: self.edit_item_values(name),
                bg="#241017", fg="#ffdce5", activebackground=COLORS["red_dark"],
                activeforeground="white", relief="flat", bd=0,
                highlightthickness=1, highlightbackground="#7d2940",
                font=("Segoe UI Semibold", 9), cursor="hand2",
                padx=18, pady=8,
            ).grid(row=0, column=3, sticky="e", padx=(0, 16))
        if not visible:
            tk.Label(
                self.items_frame,
                text="No inventory records match this search.",
                bg=COLORS["panel"], fg=COLORS["muted"],
                font=("Segoe UI", 10), padx=24, pady=32,
            ).grid(row=1, column=0, sticky="ew")

    def edit_item_values(self, identifier: str) -> None:
        if not self.save:
            return
        try:
            item = self.save.read_item_attributes(identifier)
        except (SaveFormatError, OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return

        window = tk.Toplevel(self)
        window.title(f"{APP_TITLE} // ITEM VALUES")
        window.configure(bg=COLORS["black"])
        popup_width = 720
        popup_height = min(780, max(680, window.winfo_screenheight() - 110))
        popup_x = max(0, (window.winfo_screenwidth() - popup_width) // 2)
        popup_y = max(0, (window.winfo_screenheight() - popup_height) // 2 - 10)
        window.geometry(
            f"{popup_width}x{popup_height}+{popup_x}+{popup_y}"
        )
        window.minsize(680, 600)
        window.transient(self)
        panel = ttk.Frame(window, padding=22, style="Panel.TFrame")
        panel.pack(fill="both", expand=True, padx=14, pady=14)
        ttk.Label(
            panel, text=identifier, style="Title.TLabel",
            font=("Segoe UI Semibold", 15),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        attributes = item.get("attributes", {})
        unknown = item.get("unknown", {})
        category = SOURCE_CATEGORY_INDEX.get(identifier, "")
        is_weapon = category in {
            "CategoryType_Melee", "CategoryType_Firearm", "CategoryType_Bow",
            "CategoryType_Crossbow", "CategoryType_Weapon",
        }
        damage_overrides = self._load_weapon_damage_overrides()
        current_damage = damage_overrides.get(
            identifier, self._source_weapon_damage(identifier)
        )
        variables = {
            "quantity": tk.StringVar(value=str(item.get("quantity", 1))),
            "condition": tk.StringVar(value=str(item.get("condition", -1))),
            "repairs": tk.StringVar(value=str(item.get("repairs", 0))),
            "color": tk.StringVar(value=str(attributes.get("color", "white"))),
            "power": tk.StringVar(value=str(unknown.get("unknown008", -1))),
            "craftPlan": tk.StringVar(value=str(item.get("craftPlan", "None"))),
            "damage": tk.StringVar(value=f"{current_damage:g}"),
        }
        fields = [
            ("Quantity", "quantity"),
            ("Condition / durability", "condition"),
            ("Repairs used", "repairs"),
            ("Rarity", "color"),
            ("Weapon runtime value", "power"),
            ("Blueprint / craft plan", "craftPlan"),
        ]
        if is_weapon:
            fields.insert(
                1, ("Save-only damage target (category-wide, max 1,000,000)", "damage")
            )
        for row, (label, key) in enumerate(fields, start=1):
            ttk.Label(panel, text=label, style="Panel.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 18), pady=6
            )
            if key == "color":
                ttk.Combobox(
                    panel, textvariable=variables[key],
                    values=("white", "green", "blue", "violet", "orange", "platinum"),
                    state="readonly",
                ).grid(row=row, column=1, sticky="ew", pady=6)
            else:
                ttk.Entry(panel, textvariable=variables[key]).grid(
                    row=row, column=1, sticky="ew", pady=6
                )
        existing_sockets = [
            str(value) for value in item.get("upgradeSockets", [])
            if str(value) != "None"
        ]
        socket_vars = [
            tk.StringVar(
                value=existing_sockets[index]
                if index < len(existing_sockets) else "None"
            )
            for index in range(4)
        ]
        socket_row = len(fields) + 1
        ttk.Label(panel, text="Upgrade sockets", style="Panel.TLabel").grid(
            row=socket_row, column=0, sticky="nw", padx=(0, 18), pady=6
        )
        socket_frame = ttk.Frame(panel, style="Panel.TFrame")
        socket_frame.grid(row=socket_row, column=1, sticky="ew", pady=6)
        socket_frame.columnconfigure(0, weight=1)
        socket_frame.columnconfigure(1, weight=1)
        for index, socket_var in enumerate(socket_vars):
            row_frame = ttk.Frame(socket_frame, style="Panel.TFrame")
            row_frame.grid(
                row=index // 2, column=index % 2, sticky="ew",
                padx=(0, 8) if index % 2 == 0 else (8, 0), pady=3,
            )
            row_frame.columnconfigure(1, weight=1)
            ttk.Label(
                row_frame, text=f"Slot {index + 1}", style="Muted.TLabel", width=8
            ).grid(row=0, column=0, sticky="w")
            ttk.Combobox(
                row_frame,
                textvariable=socket_var,
                values=SOCKET_UPGRADES,
                state="readonly",
            ).grid(row=0, column=1, sticky="ew")
        panel.columnconfigure(1, weight=1)

        def apply_values() -> None:
            try:
                power_value = int(variables["power"].get())
                if not -1 <= power_value <= 255:
                    raise ValueError(
                        "Weapon runtime value must be between -1 and 255. "
                        "This field is not raw damage."
                    )
                damage_value = float(variables["damage"].get())
                if is_weapon and not 1 <= damage_value <= 1_000_000:
                    raise ValueError(
                        "Weapon damage must be between 1 and 1,000,000."
                    )
                values = {
                    "quantity": int(variables["quantity"].get()),
                    "condition": float(variables["condition"].get()),
                    "repairs": int(variables["repairs"].get()),
                    "color": variables["color"].get(),
                    "power": power_value,
                    "craftPlan": variables["craftPlan"].get().strip(),
                    "upgradeSockets": [
                        socket.get() for socket in socket_vars
                        if socket.get() and socket.get() != "None"
                    ],
                }
                self.save.update_item_attributes(identifier, values)
                if is_weapon and damage_value != current_damage:
                    self._set_weapon_damage_override(
                        identifier, damage_value, window
                    )
            except (ValueError, SaveFormatError, OSError, json.JSONDecodeError) as exc:
                messagebox.showerror(APP_TITLE, str(exc), parent=window)
                return
            self.quantity_vars.clear()
            self._show_entries()
            window.destroy()
            self.status_var.set(
                f"STAGED  •  edited {identifier}  •  Press SAVE CHANGES to write"
            )

        def op_preset() -> None:
            variables["condition"].set("999999")
            variables["repairs"].set("0")
            variables["color"].set("platinum")
            variables["power"].set("8")
            for socket in socket_vars:
                socket.set("Craft_Upgrade_DamL2DurL2BalL2")

        action_row = socket_row + 1
        ttk.Button(panel, text="RESTORE WORKING WEAPON", command=op_preset).grid(
            row=action_row, column=0, sticky="w", pady=(12, 4)
        )
        ttk.Button(
            panel, text="APPLY VALUES", style="Accent.TButton", command=apply_values
        ).grid(row=action_row, column=0, columnspan=2, sticky="e", pady=(12, 4))

    def max_visible(self) -> None:
        if not self.save:
            return
        query = self.search_var.get().strip().casefold()
        selected_category = self.inventory_category_var.get()
        for entry in self.save.entries:
            if (
                (
                    selected_category == "All categories"
                    or SOURCE_CATEGORY_INDEX.get(
                        entry.identifier, "CategoryType_Inventory"
                    ).replace("CategoryType_", "") == selected_category
                )
                and (
                    not query
                    or query in entry.display_name.casefold()
                    or query in entry.identifier.casefold()
                )
            ):
                source_limit = self._source_max_stack(entry.identifier)
                self.quantity_vars[entry.identifier].set(
                    str(source_limit if source_limit is not None else MAX_QUANTITY)
                )

    def reset_values(self) -> None:
        if not self.save:
            return
        for entry in self.save.entries:
            if entry.identifier in self.quantity_vars:
                self.quantity_vars[entry.identifier].set(str(entry.quantity))

    @staticmethod
    def _validate_quantity(value: str) -> bool:
        return value == "" or (value.isdigit() and len(value) <= 6)

    def save_changes(self) -> None:
        if not self.save or getattr(self, "_saving", False):
            return
        quantities: dict[str, int] = {}
        try:
            for identifier, var in self.quantity_vars.items():
                if var.get() == "":
                    raise ValueError(
                        f"Enter a quantity for {FRIENDLY_NAMES.get(identifier, identifier)}."
                    )
                quantities[identifier] = int(var.get())
            self.save.update_quantities(quantities)
        except (ValueError, SaveFormatError) as exc:
            messagebox.showerror(APP_TITLE, str(exc), parent=self)
            return

        if not messagebox.askyesno(
            APP_TITLE,
            "Save these changes?\n\n"
            "The game should be completely closed. A backup will be created first.",
            parent=self,
        ):
            return
        active_save = self.save
        self._saving = True
        self.save_button.configure(state="disabled", text="SAVING…")
        self.status_var.set("SAVING  •  creating backup and validating save…")
        self.configure(cursor="watch")
        self.update_idletasks()
        self._save_result_queue: queue.Queue = queue.Queue(maxsize=1)
        started = time.perf_counter()

        def worker() -> None:
            try:
                backup = active_save.write_safely()
                loaded = DyingLightSave.load(active_save.path)
                self._save_result_queue.put(("ok", loaded, backup, started))
            except Exception as exc:
                self._save_result_queue.put(("error", exc, None, started))

        threading.Thread(
            target=worker, name="dlse-save-writer", daemon=True
        ).start()
        self.after(40, self._poll_save_result)

    def _poll_save_result(self) -> None:
        try:
            status, payload, backup, started = self._save_result_queue.get_nowait()
        except queue.Empty:
            self.after(40, self._poll_save_result)
            return
        self.configure(cursor="")
        self._saving = False
        self.save_button.configure(state="normal", text="SAVE CHANGES")
        if status == "error":
            self.status_var.set("SAVE FAILED  •  original file was left protected")
            messagebox.showerror(
                APP_TITLE,
                f"The save was not updated safely:\n{payload}",
                parent=self,
            )
            return

        self.save = payload
        item_total = sum(entry.quantity for entry in self.save.entries)
        self.dashboard_values["file"].set(self.save.path.name)
        self.dashboard_values["records"].set(f"{len(self.save.entries):,}")
        self.dashboard_values["units"].set(f"{item_total:,}")
        self.dashboard_values["skills"].set(f"{len(self.save.skills):,}")
        self.dashboard_values["decoded"].set(
            f"{len(self.save.decoded):,} bytes"
        )
        self.dashboard_values["integrity"].set("VALID & PROTECTED")
        elapsed = time.perf_counter() - started
        self.status_var.set(
            f"SAVED  •  {elapsed:.2f}s  •  Backup: {backup.name}"
        )
        messagebox.showinfo(
            APP_TITLE,
            f"Save updated successfully in {elapsed:.2f} seconds.\n\n"
            f"Backup created in:\n{backup.parent}",
            parent=self,
        )


if __name__ == "__main__":
    SaveEditorApp().mainloop()
