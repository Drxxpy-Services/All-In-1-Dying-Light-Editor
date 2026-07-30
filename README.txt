DYING LIGHT // SAVE ARCHITECT

Keep these files and the runtime_mods folder together.

RUN
1. Close Dying Light.
2. Open DyingLightSaveEditor.py with Python.
3. Select Runtime Mods in the left sidebar.
4. Confirm the detected Dying Light folder.
5. Use INSTALL / UPDATE on either or both runtime packages.
6. Launch Dying Light. The developer controls are accessed from the pause menu.

RUNTIME PACKAGES
- Selvenik Developer Menu: pause-menu cheats, locations, items, XP, storage,
  missions, collectables, vehicle tools, and debug pages.
- God Mode + Survival Rules: extreme health and stamina, regeneration,
  stamina/fall/damage rule changes for DW_DLC1 / The Following.

PER-WEAPON DAMAGE
- Open Inventory, locate a weapon, and select EDIT VALUES.
- Enter 1 to 1,000,000 in In-game weapon damage.
- APPLY VALUES writes an oversized Legend damage multiplier into the save.
- No runtime damage package is required.
- Dying Light stores this multiplier by category, so editing a rifle boosts all
  firearms; one-handed, two-handed, and bow damage use their own categories.
- Durability, repairs, rarity and sockets are stored in the save.
- Close Dying Light before saving changes.

VERIFIED ULTRA-DAMAGE PROFILE
- Developer Tools includes the exact save-only ranks recovered from the supplied
  "Ultra Damage Weapons" save.
- Applying the profile records the six existing damage ranks before changing them.
- REVERT ULTRA DAMAGE restores those exact original ranks and stages the result;
  press SAVE CHANGES afterward to write the restored values to the save.
- For a profile applied by an older editor with no snapshot, revert uses the
  normal fallback rank of 25 for the six affected damage categories.
- Unarmed, one-handed and two-handed damage: Legend rank 5,000.
- Firearms, bows and throwing damage: Legend rank 8,000.
- The reference save shows a semi-automatic shotgun at 2,042,550 firepower.
- Newly acquired weapons also receive the boost because it is category-wide.

CHEAT ENGINE WORKSPACE
- The Cheat Engine tab detects a local Cheat Engine installation or lets you
  browse to its executable.
- Add named addresses/module offsets and choose the correct value type.
- EXPORT TABLE creates a standard .CT file.
- LAUNCH & ATTACH opens the generated table and automatically attaches to
  DyingLightGame.exe when the game is running.
- Fixed addresses commonly change after restarting the game. Prefer verified
  pointers, module offsets or symbols created by AOB scripts.
- Synsteric's DL1 Workstation 1.1.3 is included as a built-in table. It contains
  814 entries and targets Dying Light 1.53.
- The table includes player, inventory, weapon, no-ammo, god-mode, teleport,
  world, AI, vehicle, shop, pointer and debugging tools.
- The supplied Lua contains no downloader or DLL injection. An optional creator
  profile entry opens Synsteric's Nexus Mods profile in the web browser.

SAFETY
- Existing game files receive a .save_architect_backup copy before replacement.
- DISABLE / RESTORE restores that exact original file.
- Files that did not exist before installation are marked and removed safely.
- Close the game before installing or restoring packages.
- Steam Verify Files can also restore official files if another mod changed them.

ONLINE PLAY
Use runtime modifications in single-player or with consenting friends. Modified
game rules can cause version mismatches or unwanted behavior in public sessions.
