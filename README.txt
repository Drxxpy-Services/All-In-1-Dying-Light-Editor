Dying Light // Save Architect

A modern Python save editor and modding workspace for **Dying Light 1 on Steam**.

> Close Dying Light before editing. The editor creates automatic backups, but you should always keep your own copy of important saves.

## Main Features

| Tab | Features |

|---|---|

| **Dashboard** | Save overview, record counts, decoded size, skills, and integrity status |

| **Inventory** | Search, category filters, quantities, item values, and weapon editing |

| **Item Spawner** | Search roughly 1,500 source definitions and add supported items |

| **Skills** | Search, lock, unlock, set ranks, and max skill trees |

| **Player Progression** | Money, health, fury, time, days, and progression presets |

| **Developer Tools** | Ultra Damage, weapon repair, outfits, money, skills, health, and time |

| **Runtime Mods** | Install, update, disable, and restore optional mod packages |

| **Cheat Engine** | Build, export, launch, and attach `.CT` tables |

| **Save Inspector** | Expandable Key / Value / Type view of decoded save data |

| **Backups** | Review timestamped backups created before save writes |

## Installation

1. Download or clone the repository.
2. Keep the Python file, `runtime_mods`, and `cheat_tables` together.
3. Install a modern version of Python 3 with Tkinter.
4. Close Dying Light.
5. Run:

```powershell
python DyingLightSaveEditor.py
```

Typical Steam save location:

```text
Steam\userdata\<Steam ID>\239140\remote\out\save\save_coop_0.sav
```

## Inventory and Weapons

- Edit quantity, durability, repairs, rarity, blueprint, and runtime value
- Select up to four upgrades from socket dropdowns
- Set save-only weapon damage from `1` to `1,000,000`
- Restore broken weapons using verified working values
- Search inventory records by name, ID, or category

> Oversized weapon damage is category-wide. Editing a rifle can affect other firearms; melee, bows, and throwing weapons use separate Legend categories.

## Item Spawner

- Search by name or internal ID
- Filter by category or quick-filter buttons
- Inspect source-defined item properties
- Choose a quantity and add supported items
- Add all supported catalogue items
- Add every normal craft material at `999,999` with one button

Some internal test records may not behave like normal player items.

## Skills and Progression

- Lock, unlock, rank, or max selected skills
- Max Runner, Fighter, Survivor, Driver, Legend, or all trees
- Max health upgrades
- Edit carried and stash money
- Edit health, fury, elapsed days, and time
- Set day or night instantly

## Developer Tools

- Verified Ultra-Damage Save Profile
- Revert Ultra Damage
- Repair Broken Weapon Values
- Unlock Collectible Outfits
- Max Money
- Max All Skill Trees
- Max Health Upgrades
- Set Day / Set Night

### Ultra-Damage Profile

| Category | Rank |
|---|---:|
| Unarmed / One-handed / Two-handed | 5,000 |
| Firearms / Bows / Throwing | 8,000 |

The editor saves the original six ranks before applying the profile. **Revert Ultra Damage** restores that snapshot. Older profiles without a snapshot fall back to rank `25`.

## Runtime Mods

Included support:

- Selvenik Developer Menu
- God Mode + Survival Rules

Original game files receive `.save_architect_backup` copies before replacement. Disable or restore a package to recover those files.

## Cheat Engine

- Detect or browse to Cheat Engine
- Add addresses and module offsets
- Select value types
- Export standard `.CT` files
- Launch and attach to `DyingLightGame.exe`
- Use the included Synsteric's DL1 Workstation 1.1.3 table

Fixed addresses may change after restarting the game. Verified pointers and AOB scripts are more reliable.

## Safe Saving

1. Close Dying Light.
2. Open the correct save.
3. Stage and review changes.
4. Press **Save Changes**.
5. Let the editor create and validate its backup.
6. Test the save in-game.

Backups are stored in `DLSE Backups` beside the original save.

## Project Links

- [GitHub](https://github.com/Drxxpy-Services)
- [Discord](https://discord.com/invite/Ckp6wzx974)
- TikTok: [@captain_stains](https://www.tiktok.com/@captain_stains)
- TikTok: [@unknownbooster](https://www.tiktok.com/@unknownbooster)
- TikTok: [@aydenjames369](https://www.tiktok.com/@aydenjames369)
- YouTube: [@Warp_Clock](https://www.youtube.com/@Warp_Clock)
- Twitch: Coming soon

## Credits

**Creator:** Ayden  
**Lead Developers:** CaptainStains, Poncho, Unknown

## Disclaimer

Independent community project. Not affiliated with Techland or Valve. Use modified saves and runtime mods in single-player or with consenting friends.
