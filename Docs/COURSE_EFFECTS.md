# Original course effects and audio

The read-only audit uses course revision 992f860. Acquired third-party assets and
all generated presentation assets remain in ignored local folders. Gameplay uses
native asset references; ExternalAssets.json is used by installation/editor setup.

| Mechanic | Original presentation |
| --- | --- |
| Cast | NS_Portal_Cast + MSS_Combat_Abilities_Primary_Cast |
| Projectile flight | NS_Gideon_Primary_Projectile + MSS_Combat_Abilities_Primary_Loop |
| Projectile hit | NS_Gideon_Primary_HitWorld + MSS_Combat_Abilities_Primary_Impact |
| Black hole | NS_Gideon_Ultimate + MSS_Combat_Abilities_Secondary_Loop |
| Teleport impact | NS_Portal_Entrance_Close + MSS_Combat_Abilities_Dash_Impact |
| Sprint | NS_Gideon_TravelMode_Hands on Muzzle_02 and Muzzle_01 + MSS_PlayerLocomotion_Hover |
| Local player stun | MSS_Player_StatusEffects_Stunned + SCM_Stunned |
| Barrel fuse | NS_Flames + MSS_Environmental_BarrelAftermath |
| Barrel explosion | NS_Explosion + MSS_Environmental_BarrelExplode |
| Health potion | MSS_Consumables_HealthPotion |
| Chest | Original placed TreasureBurst Niagara + MSS_Interactables_TreasureChestOpen |
| Coins | Original M_Pickup_Coin material animation + MSS_Interactables_CurrencyPickup / CoinPickedUp |

Sprint returns both hand systems to Niagara's pool and sends StopHovering to the
MetaSound. Stun sends EffectFinished and balances Push/PopSoundMixModifier.
Component references used by actions are strong reflected fields. The independent
one-shot portal effect outlives its projectile; the projectile trail deactivates
without hiding the entire actor, matching the original.

Install with `setup_external_assets.py --with-course-effects --with-minions
--with-course-animation --source-content <acquired-project>/Content`, then
`install_course_world.py --source-content <acquired-project>/Content`.
Run `Scripts/prepare_course_effects.py` in the editor to refresh the local profile
and original-layout map. The `rogue-course-effects` suite verifies real audio and
Niagara lifecycle. Its launcher removes benchmark mode, which disables Unreal's
audio engine even when -NoSound is absent.

`rogue-course-effects-v10-20261105` completed all ten audio/Niagara lifecycle checks
and strict EndPIE gates. Clean gameplay spawned 1000 coins in 5.22 ms during this
audio-enabled run. A final clean-start run also validates the test fixture cleanup.

Final clean-start validation: rogue-bulk-fx-final-v11-20261105 PASS.
Program-cache/fresh-process artifact loading and all ten audio/Niagara checks
passed, including strict EndPIE cleanup and removal of test actors from the map.
