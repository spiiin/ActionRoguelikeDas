# Проверка порта

Дата: 1 ноября 2026 года. Движок: локальная Unreal Engine 5.8.3, Win64 Editor Development. Интеграция: C:/src/DasForUE2-main.

## Пройденные проверки

- Сборка DasForUESmokeEditor: PASS.
- DasForUE.Ports.RogueChest: PASS, 1 тест, 0 предупреждений, 0 ошибок.
- Foundation: PASS, failures=0.
- Interface contracts: PASS.
- Inherited handlers: PASS, 34 проверки.
- clang-format нового C++ теста, синтаксис PowerShell runner и JSON проекта: PASS.

Целевой тест выполняет интерфейс и сундук из исходников проекта порта в настоящем игровом UWorld с NullRHI. Проверяет членство базового и дочернего классов в интерфейсе, вызов daScript → UE interface → daScript, отказ для пустой ссылки и неподходящего Actor, создание компонентов и attachment, скорость и конечный угол, мировой поворот крышки, сохранение её положения и масштаба, две независимые копии, повторное взаимодействие, отрицательный целевой угол и отключение tick. Событие завершения переопределено в тестовом дочернем daScript-классе. Мир завершается через EndPlay.

## Записи результатов

Финальный запуск через общий агент: rogue-chest-20261101-07.

- C:/src/DasForUE2/logs/agent/rogue-chest-20261101-07.log — DAS_SUITES=PASS.
- C:/src/DasForUE2-main/logs/rogue-chest-report/index.json — succeeded=1, succeededWithWarnings=0, failed=0, notRun=0.
- C:/src/DasForUE2/logs/agent/rogue-chest-20261101-05.log — отдельные PASS для interface-contracts, foundation и dsl-inherited-handlers.

Тест временно подключает collision-конфигурацию порта к smoke-проекту и восстанавливает исходные байты файла после запуска. Копии скриптов и сгенерированные test assets исключены из Git интеграции. Тест внешнего порта выполняется только с флагом DasRoguePort; runner передаёт его автоматически.

## Границы проверки

Визуальная проверка карты в PIE, ввод с физических устройств, горячая перезагрузка и packaged build в этот запуск не входят. Самостоятельный ActionRoguelikeDas.uproject подготовлен; игровая проверка выполнена через smoke-проект DasForUE, а не через отдельную сборку этого проекта.

## Компонент и контроллер — 2 ноября 2026

`rogue-input-20261102-test4`: сборка PASS; `DasForUE.Ports.RogueInteractionPIE` PASS, succeeded=1, succeededWithWarnings=0, failed=0. Отчёт: C:/src/DasForUE2-main/logs/rogue-interaction-report/index.json. Лог агента: C:/src/DasForUE2/logs/agent/rogue-input-20261102-test4.log.

Проверяется настоящий PIE, GameMode с новым daScript PlayerController, созданный через SCS скриптовый ActorComponent, TeamId=1, Enhanced Input с Boolean IA и mapping E. Ввод подаётся через штатный PlayerController.InputKey. До нажатия сундуки закрыты; удержание E 0,5 секунды даёт ровно один вызов; открывается только выбранная цель. Далее проверяются окончание анимации, отсутствие взаимодействия вне радиуса, удаление выбранного сундука с переходом к оставшемуся, отсутствие pawn и ноль persistent runtime contexts после EndPIE.

В `rogue-input-20261102-regression` отдельно прошли actor-host и adapter-input-events. Foundation затем потребовал обновить обязательный Bindings/FoundationExterns.txt двумя новыми extern-функциями; манифест обновлён. Фоновый редактор первоначально помешал линковке NetCore; это устранено последовательным запуском сборок и редактора.

Игра (интерфейс, сундук, выбор цели и обработка E) реализована на daScript. C++ добавляет универсальную поддержку PlayerController в DasForUE и тестовое окружение.

Регрессии после обновления манифеста: rogue-input-20261102-regression3 — DAS_SUITES=PASS. Interface contracts PASS; Foundation PASS failures=0; inherited handlers PASS 34 проверки; rogue-chest PASS (1 тест, 0 предупреждений, 0 ошибок). Новые C++ файлы проходят clang-format --dry-run --Werror, diff --check чистый, синтаксис PowerShell и Python проверен.



## RogueProjectile — 2 ноября 2026

Целевой запуск через общий агент: `rogue-projectile-20261102-test6` — DAS_SUITES=PASS. `DasForUE.Ports.RogueProjectilePIE`: 1 тест, 0 предупреждений, 0 ошибок. Отчёт C:/src/DasForUE2-main/logs/rogue-projectile-report/index.json; лог C:/src/DasForUE2/logs/agent/rogue-projectile-20261102-test6.log.

Тест выполняется в настоящем PIE с рендерингом и аудио (RenderOffscreen, без NullRHI/nosound). Проверены: отсутствие автоматического выстрела; LMB через PlayerController.InputKey и Enhanced Input; ровно один выстрел при удержании; Sphere root радиусом 16 как UpdatedComponent; скорость 2000 и нулевая гравитация; движение через world ticks; Owner=controller и Instigator=pawn до BeginPlay; исключение pawn из swept movement; срок жизни 30 секунд; наличие LoopedNiagara/Audio; попадание в стену и Destroy; активный world-owned RadialBurst после уничтожения снаряда; второй выстрел и отдельное истечение lifetime; очистка persistent contexts после EndPIE.

Отдельные проверки внутри теста: копирование native FHitResult в CollisionHit, независимость копии от исходной памяти, сохранение геометрии/флагов/времени, отказ для non-finite payload и неверного ожидаемого типа.

Предыдущие прогоны выявили отсутствующую поддержку callback HitResult и канонического native struct declaration; добавлены owned collision projection и его регистрация. Неэкспортированный Actor.GetInstigator заменён существующим native property Instigator.

Первый этап ранее проверен пользователем вручную: E открывает сундук нормально. В этом этапе сохраняется тот же контроллер и взаимодействие E. Качество звучания, художественный вид эффекта и packaged build отдельно не оценивались.

Регрессия rogue-projectile-20261102-regression: Foundation PASS, MethodValues PASS (530 секунд), ActorIsolation/Actors.SpawnPIE/MethodValues.PIE PASS. Gameplay.RuntimePIE выявил несовместимое расширение ActorAdapter-проверки defaults на старые Pawn/Character. Условие ограничено прежними хостами и новым PlayerController; повторная проверка — rogue-projectile-20261102-regression2.
Карта подготовлена скриптом prepare_projectile.py: Saved/Logs/ProjectilePrepare.log содержит DAS_ROGUE_PROJECTILE_EDITOR_READY. Сохранены IA_Fire, IMC_Rogue с ЛКМ, BP_ProjectileDemo, обновлённый контроллер и стена-мишень.



## Исправления после ручной проверки

В сохранённом IMC_Rogue отсутствовала ЛКМ: MapKey не помечал существующий package dirty. Подготовка теперь использует Modify и явный save_packages(..., False) для конкретных input assets. После отдельного перезапуска MCP подтвердил загруженные с диска пары IA_Interact/E и IA_Fire/LeftMouseButton.

OnComponentHit вызывал K2_DestroyActor внутри активного VM callback, и вложенный EndPlay не проходил авторизацию. Добавлен универсальный ue_actor_destroy_self с ActorLifecycleTarget guard; RogueProjectile использует его. Runner теперь отклоняет сообщения `daScript lifecycle ...:` и `daScript did not run`, даже если Unreal Automation отметил тест успешным.

rogue-projectile-20261102-self-destroy: build PASS, rogue-interaction PASS, rogue-projectile PASS, каждый 1 тест/0 предупреждений/0 ошибок, DAS_SUITES=PASS; дополнительных lifecycle error сообщений нет. regression2 также завершился DAS_SUITES=PASS, включая исправленный Gameplay.RuntimePIE, Foundation и 51 event check.

MCP: stdio initialize/ListTools PASS (40 tools); discovery автоматически нашёл ActionRoguelikeDas на UE 5.8.3; ue_python работает после перезапуска без ручного включения Remote Execution. Сохранённый mapping прочитан через MCP. Реальный PIE запускается через LevelEditor CDO command API.

Финальная проверка через MCP после перезапуска: загруженный IMC_Rogue содержит IA_Interact/E и IA_Fire/LeftMouseButton; настоящий PIE запущен через native LevelEditor command; InjectInputVectorForAction(IA_Fire) дал ProjectilesFired=1, LastDasError пуст, live projectiles=[] после попадания. В McpEditor.log ноль сообщений daScript lifecycle BP_ProjectileDemo / daScript did not run. Remote Execution был доступен автоматически с новым PID редактора.


## Blueprint editor crash — 2 ноября 2026

При открытии BP_ProjectileDemo редактор падал в UAnimBlueprintExtension_PropertyAccess::HandleStartCompilingClass во время подготовки Blueprint action database. В проекте DisableEnginePluginsByDefault отключал стандартный PropertyAccessEditor. В ActionRoguelikeDas.uproject добавлено явное включение PropertyAccessEditor; исходники движка не изменялись.

Проверка: новый запуск Unreal, в McpEditor.log подтверждены подключение плагина и загрузка его DLL. Через ue_python открыт /Game/DasRogue/BP_ProjectileDemo; после прогрева редактор продолжил отвечать через MCP, CDO InitialSpeed=2000.0, процесс Responding=True. В новом логе нет Fatal error / Unhandled Exception. Изменение скорости не выполнялось.

Content Drawer: явно включён ContentBrowserAssetDataSource в порте и smoke target DasForUE; build-editor content-browser-20261102 PASS. После перезапуска MCP подтвердил active_sources=['AssetData'], 14 ассетов /Game/DasRogue и по одному ContentBrowser item для папки /All/Game/DasRogue и /All/Game/DasRogue/BP_ProjectileDemo.BP_ProjectileDemo. Перед перезапуском PIE остановлен, save_dirty_packages=True.

## Projectile spawn hitch diagnosis — 2 ноября 2026

Measured in current ChestTest PIE through MCP Python perf_counter around reflected controller OnFire(True), without changing saved gameplay assets. First five calls: 329.792, 321.570, 319.128, 315.271, 311.363 ms. Repeated A/B: normal 322.192,315.359,310.377,312.832,314.014 ms; same Blueprint/components with CDO LifecycleScript temporarily empty: 2.041,1.186,0.979,0.953,1.041 ms; original LifecycleScript restored in finally, normal again 313.916,310.461,310.928,316.399,327.806 ms.

Code path: DasActorSpawn.inl ActorSpawnInstigated -> FinishSpawning -> FDasActorHostRuntime::BeginPlay -> RunLifecycle/RunCallback. In DasRuntimeModuleExecution.inl, session lookup is keyed by Owner+Path; each new owner has empty AttemptedSources, so bChanged=true and DSLCompile is called synchronously. No shared compiled-program cache on this path. DasAuthoredRefs.inl DSLCompile can perform two compilation passes for computed defaults. The A/B timings isolate total lifecycle cost, not individual compiler phases. No performance fix applied yet. Required direction: share immutable compiled program/module ownership by validated source revision while retaining independent per-owner VM/global/event state and hot-reload validation.

## Cube chest rear hinge — 2 ноября 2026

Original ARogueItemChest attaches LidMeshComponent to BaseMeshComponent and rotates the lid mesh; correct pivot comes from the asset. The engine Cube used by our demo has a centre pivot, which made the cover cut through the solid body.

Added rogue_hinged_chest.das / BP_InteractiveChestHinged: animated LidMeshComponent is an empty hinge at (-51.25,0,50) in body-local coordinates; LidVisual is attached at (51.25,0,7.5), scale (1.025,1.04,0.15). Base dimensions remain 200x130x100 cm. All gameplay and animation remain in the existing daScript base. New sample Blueprint avoids unsupported component-composition migration of an already authored class. Replaced only the old interactive chest on ChestTest, preserving actor placement and animation settings. prepare_interaction.py imports/migrates the hinged sample; configure_chest_geometry.py removes old centre-pivot overrides. Blueprint and map saved.

PIE verification via MCP: separating-axis polygon test in body-local XZ plane using actual component world transforms at 121 pitch angles (0..120 inclusive), no interior overlap. Lid and body overlap in Y, so XZ separation rules out volume intersection. Interact started the real daScript animation; CurrentAnimationPitch reached 120, LastDasError empty. EndPIE restored the saved closed chest. Test script: Tests/verify_chest_geometry.py (run in PIE; also starts Interact animation).


## Health / magic projectile — 2 ноября 2026

Implemented RogueAttributeComponent (100 HP, clamp, IsAlive, signed ApplyHealthChange,
no-op suppression, LastInstigator, OnHealthChanged), RogueMagicProjectile (25 damage,
8-second lifetime) and RogueTargetDummy (HP text, green-to-red material, delayed death).
Controller ProjectileClass now points to BP_MagicProjectileDemo. ChestTest contains
one target at (220,100,100); the chest and E interaction are retained. No course assets.

Original health-slice contract: RogueImpactHandler.ApplyProjectileDamage(Actor):bool.
The subsequent point-impact stage adds a CollisionHit argument (see below). The
base owns the single managed hit subscription, guards repeat hits, dispatches the
interface, emits effects and calls ue_actor_destroy_self_next_tick. The new generic
native helper preserves source lifetime until queued OnTakeAnyDamage notifications
are delivered, without weakening callback identity/lifetime validation or changing
existing immediate self-destruction. Program-cache/VM optimization files untouched.

Build rogue-health-20261102-build PASS (136s). Final shared-agent run
rogue-health-20261102-regression2: Foundation PASS (30s), RogueInteractionPIE PASS
(31s), RogueProjectilePIE PASS (31s), 0 warnings/errors in each game automation test,
DAS_SUITES=PASS. An initial Foundation run caught a missing const qualifier in the
new extern baseline; baseline was corrected to the generated signature before the
successful run. Existing projectile regressions stage the original no-damage
controller class default intentionally; health behavior has a separate test.

Tests/verify_health_pie.py PASS in actual rendered PIE via MCP, 8.63s. No synthetic
hit/movement injection: four distinct Enhanced Input presses, native projectile
movement and collision. HP 100->75->50->25->0, correct text, material colors
(0.25,0.75,0.05), (0.5,0.5,0.05), (0.75,0.25,0.05), (1,0,0.05). LastInstigator is
DefaultPawn for every hit. Exactly one health-change notification per hit, source
projectiles destroyed, target destroyed at zero. Also tested -10 damage, clamped
healing to max, zero/no-change suppression, IsAlive before/after death. JSON receipt:
Saved/Tests/rogue_health_pie.json. Final HealthEditor.log contains no lifecycle or
managed-handler failures and no import rejections.

Generated projectile Blueprints were recreated with backups during interface
schema migration (Saved/Backups/HealthProjectileMigration); existing BP_ProjectileDemo
InitialSpeed=250 was preserved, magic demo remains 2000. Obsolete draft interfaces
were removed after checking no asset referencers. EndPIE restored the target to
100 HP; editor left open on the saved map. No packaged/network validation for this
new stage. AI noise, point damage, physical impulses and action effects deferred.

## Existing authored interface migration - 2026-11-02

DasEditor now migrates an existing authored Blueprint interface in place, with
stable interface identity and method IDs. It updates signatures and message nodes,
handles method addition/removal and stable-ID rename, and reimports affected DAS
implementers from consistent source files. Function/event transitions regenerate
owned frame and event bridges. Connected incompatible pins, custom defaults,
unrelated implementation layout changes and unsafe user-authored bridge branches
are rejected. Structural migration requires stopped PIE and the bounded supported
asset dependency scope. Failure restores graphs, pins, references, contracts,
class defaults and dirty flags; no automatic package save is performed.

Final shared-agent interface-migration-20261102j: interface-contracts PASS (60s),
29 new migration checks PASS, existing create/export/reopen checks PASS,
DAS_SUITES=PASS. Regression interface-migration-20261102-regression: build PASS,
Foundation PASS (19s), RogueInteractionPIE PASS (22s), RogueProjectilePIE PASS (36s),
DAS_SUITES=PASS. clang-format --dry-run --Werror and git diff --check passed.

Installed DasRuntime/DasEditor binaries from the successful main smoke build into
this project with the matching engine BuildId 33869b21-4834-4218-8534-c32270a5e55c.
Normal editor is running on ChestTest. MCP verification in InterfaceEditor.log:
DAS_INTERFACE_APPLY PASS 1 for rogue_projectile_impact_interface.das;
target_ready True; chest_ready True. No gameplay or program-cache optimization
changes were made as part of this interface-migration extension.


## RogueCharacter movement/camera slice - 2026-11-02

BP_RogueCharacter now replaces DefaultPawn in BP_RogueGameMode. Canonical source
is Content/Das/Scripts/rogue_character.das. Movement basis, input handlers, setup,
jump and release are daScript. Added only a native type declaration for
SpringArmComponentRef to the wrapper; no C++/native host/build or optimization
changes required. Native CharacterMovement settings are assigned in BeginPlay
from editable script values. SCS camera attaches to SpringEndpoint. Temporary
engine Cone visual has NoCollision; native capsule owns movement/collision.

Scripts/prepare_character.py creates independent IMC_Character (priority 1),
IA_Move/Look/Jump and leaves IMC_Rogue/E/LMB intact. Fixed a real S-backwards bug:
map_key returns a Python struct copy; its Negate/Swizzle edits must be written
back via DefaultKeyMappings.Mappings. Final mappings persist across editor reopen.

Tests/verify_character_pie.py PASS twice, 15.50s then 11.08s after complete editor
reopen. W/S move +111/-111 cm along camera yaw; D/A +111/-111 cm on right axis;
yaw 90 rotates movement basis. Native Enhanced Input injection uses the modifiers
from each saved key mapping (not OS keyboard events). Mouse X/Y independently
change controller rotation and orbit actual camera. Jump rises about 115.56 cm,
one Started/Completed pair, lands. E animates chest; LMB spawns one projectile
with actual native flight/collision and target HP 100->75. No LastDasError.
Receipt: Saved/Tests/rogue_character_pie.json. Test hold windows accommodate
background PIE throttling; initial shorter mouse windows injected no frame.

Existing Tests/verify_health_pie.py now aims from actual camera-manager location
for third-person support. PASS 8.95s: four hits 100->75->50->25->0, correct material
colors/text, BP_RogueCharacter as instigator, exactly four shots, source projectile
and target destruction, clamping and no-op checks retained. Receipt:
Saved/Tests/rogue_health_pie.json. Python AST syntax checks passed. Full compiled
Foundation/other suites were not rerun because no native/generated code changed.
No packaged/network/physical-device tests. Source permission remains pending.

Remaining character work: projectile muzzle on character with camera targeting,
player health/death and action system. Existing controller still fires from camera.


## Character muzzle, health and terminal death - 2026-11-02

All gameplay remains daScript. Controller aims using camera Visibility trace,
ignoring its pawn, then spawns 75 cm forward (camera yaw) and 40 cm above pawn.
Sphere sweep radius 16 clips muzzle before cover; penetration or a target behind
muzzle rejects firing. Owner/Instigator and single Started press semantics kept.
Character owns existing RogueAttributeComponent plus camera-facing HP label. H
applies 25 native damage for manual verification. Death once stops jump/velocity,
sets MOVE_None and disables Character/Controller input plus move/look. Capsule
blocks Projectile because the temporary visual has no skeletal collision mesh.
Gameplay needs no new native API. A compile-time cache metadata fix was required
after checking the freshly rebuilt runtime (described below).

Rendered PIE Tests/verify_character_combat_pie.py PASS 7.39s: actual target hit
100->75, muzzle 85 cm from pawn / 425.83 cm from camera; Instigator is ignored.
Near cover clips muzzle X to 369 instead of spawning past the wall at X=386;
projectile collides and target behind wall takes no damage. Real incoming magic
projectile damages the Character capsule to 75 HP. Three separate H action
presses yield 50/25/0 HP; label updates and one terminal death. Native Enhanced
Input injections after death cannot move/look/jump/fire/interact or apply H again.
Receipt: Saved/Tests/rogue_character_combat_pie.json. Test helper CombatProbe uses
ordinary daScript spawn; it contains no production combat implementation.
Python's internal-use-only BeginDeferredActorSpawn is unavailable in this UE
build, hence the probe. Probe is removed from the editor map after the test.

Tests/verify_character_pie.py PASS 11.46s with new controller, then PASS 10.99s
after the death test and fresh PIE: input resets, movement/jump/camera/E/real
projectile target hit still work. Receipt: Saved/Tests/rogue_character_pie.json.
Python AST checks and PowerShell parser checks PASS. No packaged/network/ragdoll
or respawn validation. Stop/start Play creates a fresh living player.

Final shared-agent character-combat-20261102-regression2: build PASS (14s),
RogueInteractionPIE PASS (21s), RogueProjectilePIE PASS (26s), each automation
1 success / 0 warnings / 0 errors; DAS_SUITES=PASS. Initial full build PASS
(305s) revealed missing authored method source signature in unchanged Interact
call. An interim explicit-import workaround passed those fixtures but was removed: importing
a component with owner events registers its callbacks in the Actor module. Final
fix captures/replays value-only compile-time descriptors on cached program reads.
Legacy tests stage MuzzleHeight=0 for DefaultPawn; production remains 40.
The runtime rebuild exposed this cache-metadata issue during final port verification.
The final cache fix is being validated with original lightweight reference modules.

Cache-metadata correctness fix: DSLCompile captures newly contributed value-only
method/property descriptors and reference declarations before compile-chain reset.
FCompiledProgram owns the restore closure; AcquireCompiledProgram replays it on
cache hits only inside an active declaration compilation. No AST pointers are
captured. Both ordinary and computed-default second-pass programs capture the
final metadata. Runtime contexts/callbacks are not shared or imported by this fix.
Original lightweight rogue_refs/rogue_attribute_refs dependencies restored.

Shared-agent character-combat-20261102-metadata: build PASS (312s), Foundation
PASS (86s, including Zen startup), RogueInteractionPIE PASS (31s),
RogueProjectilePIE PASS (31s), DAS_SUITES=PASS. Automation tests each report
1 success / 0 warnings / 0 errors. clang-format dry-run/Werror and selected
git diff --check PASS. This replaces the temporary explicit-import workaround.

Final installed-binary verification in CharacterCombatVerifiedEditor.log:
DAS_EDITOR_COMPILE_ALL scripts=61 failed=0; complete combat PIE PASS (9.31s)
with original typed calls/delegates. Camera/muzzle aim, near-wall collision, real
incoming projectile, H damage and terminal death all pass; no ActorComponent
handle errors or lifecycle failures. Final fresh PIE: HP=100, alive=True, all
controls bound=True, probe=False (DAS_CHARACTER_FINAL_RESTART PASS). Test probe
removed, normal ChestTest saved, PIE stopped, editor left open for user.

## Action lifetime contract (implementation verified; PIE GC test pending)

`RogueActionSystemComponent.Actions` is reflected storage. Its array elements
are strong `FObjectProperty` references, although a standalone `RogueActionRef`
contains only a weak runtime handle. `GrantAction` appends the new object before
calling `Setup`. `Outer` supplies ownership context and world resolution; it is
not the reference that keeps the action alive.

The prepared `verify_actions_pie.py` explicitly forces Unreal GC and checks:
(1) an action retained in `Actions` survives, (2) an otherwise unreferenced action
with the same Outer is collected, and (3) removing an action allows collection.
The probe observes a non-reflected weak handle and returns no orphan UObject to
Python, so observation must not accidentally keep the object alive.

Runtime attempt 2026-11-02: wrapper build6 PASS (423s); source import PASS.
GC execution remains PENDING: another shared-agent job closed the port editor
before the isolated test ran. Do not treat this as GC PASS. Standalone replay:
Tests/verify_action_gc.py (requires a PIE Character and RogueActionProbe).
The full actions test also exposed a separate factory defect: CheckedClass uses
exact authored identity, rejecting RogueActionSprint when requested through
RogueActionRef. Sprint is not yet validated or ready for user testing.

## Readability refactor and lifetime verification — 2026-11-02

Current validation supersedes the interrupted GC attempt above.
- Replaced manual degree/radian factors with math.radians/math.degrees and the
  explicit largest-float range check with math.is_finite.
- Shared the interaction-interface predicate and runtime interface-path constants;
  retained literal paths in authoring annotations. Expanded compound statements,
  named intermediate values and normalized all 29 port scripts with das-fmt.
- Updated regression fixture MuzzleHeight substitutions to tolerate whitespace.
- das-fmt --verify: 29 files PASS. Standalone math check PASS. PowerShell parse and
  fixture-substitution checks PASS.
- RogueRefactor.log: DAS_EDITOR_COMPILE_ALL scripts=70 failed=0.
- Saved/Tests/rogue_actions_gc.json: PASS for strong reflected ownership, orphan
  collection despite Outer, and collection after removal. Uses synchronous
  unreal.collect_garbage; the observer holds only an opaque weak runtime handle.
- Saved/Tests/rogue_character_pie.json: PASS, 15.01s. W/S/A/D, camera-relative
  movement at yaw 0/90, mouse look, jump/release/landing, E interaction and shot
  reducing target HP to 75 all pass after the math/readability changes.
- The separate exact-identity factory defect for derived Sprint actions remains
  unresolved. GC checks deliberately use base actions and do not validate Sprint.
- PIE and editor stopped after validation to release the shared testing machine.

## Vector constants, swizzles and complete source audit — 2026-11-02

Audited all 29 Content/Das/Scripts files and all three Tests/Das sources. Applied
zero/one vectors and zero-rotator constants wherever applicable; named chest hinge,
visual offset and scales; retained explicit one-off geometry sizes. Movement and
aiming use native ue_rotate_vector and existing native vector arithmetic. New
ue_vector_math supplies constants, native-math aliases and ue_direction_rotation.
The public imports propagate these names to generated methods on derived classes.

Added 48 readable 2/3-component xy/xyz selections and 14 assignment-capable
selections with no repeated destinations. RHS values are snapshotted to preserve
aliasing. Readonly literal constructor globals and aliases now expand safely in
authored/component defaults; compiler-injected context/lineinfo arguments are
removed when restoring literal syntax from imported initializers.

Validation through the shared build agent:
- rogue-vector-gameplay-20261102: computed-defaults PASS (43s); initial interaction
  attempt exposed missing public re-export, fixed before the following rerun.
- rogue-vector-gameplay-retry-20261102: RogueInteractionPIE PASS (31s),
  RogueProjectilePIE PASS (36s), DAS_SUITES=PASS.
- rogue-vector-default-models-20261102: all seven new vector/default checks PASS:
  exhaustive native swizzles/constants/aliasing/precision, repeated-write refusal,
  named/default and literal compilation, identical model values, mutable globals
  refused and function-produced globals refused. Overall Foundation remains FAIL
  failures=2: foundation_extern_manifest_matches_baseline (ordering; same entries)
  and type_support_manifest_matches_registry (earlier class-container capability
  change). Both mismatches were already present in rogue-vector-refactor-20261102,
  before the named-constant importer extension. They were not hidden or updated.
- Exact helper bodies also passed the standalone interpreter checks. Formatting
  verified with the official formatter. New API docs: DasForUE2-main/Docs/VectorMath.md.

Tested DasRuntime/DasEditor DLLs installed in the port, using the actual matching
engine BuildId. Editor was not independently launched during this validation.
The separate Sprint factory authored-identity defect remains outside this change.

Final named-default verification: rogue-vector-default-models-20261102 compiled
successfully and all seven new checks PASS, including separate named/literal Actor
model files with identical defaults and the two explicit pure-scalar-policy
rejections. Full Foundation now has exactly the two pre-existing manifest
mismatches noted above; the prior fixture callback/entry-point issues are resolved.

## Action factory / Sprint completion — 2026-11-02

ScriptObjectNew validates its native base with CheckedClass and validates authored
assignability via the existing ResolveAuthoredObject CDO-hierarchy check, before
NewObject. Derived actions are accepted; siblings are refused before an instance
is constructed. Same-world, live-Outer, template, abstract and teardown guards
remain. Other class APIs retain their existing validation semantics.

SprintActionClass is authored on RogueCharacter and granted in its BeginPlay.
Only the exact legacy Python bootstrap override [BP_RogueActionSprint_C] is cleared
from the component/Character CDO templates during preparation. Generic component
DefaultActions remains an independent editable setting. No gameplay logic is
implemented in Python or native C++.

Shared agent: rogue-actions-sprint-20261102 Foundation PASS (44s). Reviewed baseline
repair: extern signature sets were identical, only producer ordering differed;
TypeSupport changed only the Class adapter's existing container-property policy
and slot capabilities. Those describe reflection property support, not a promise
of complete typed class-map transport.

rogue-actions-sprint-complete-20261102: build PASS, rogue-actions PASS (61s),
DAS_SUITES=PASS. Real PIE receipt has 10 check groups, no error, 3.14s test time:
strong reflected ownership, Outer-only GC, removal GC, Actor rejection, unrelated
authored-class refusal before construction, template Outer refusal, independent
owners, cost-once and cooldown, Shift 450->720->450 with one start per press,
stun cancellation/blocking while preserving another speed modifier, death shutdown.
DAS_EDITOR_COMPILE_ALL scripts=72 failed=0; chest/target LastDasError also checked.
The editor exited after removing the editor-world probe and saving the clean map.

The new suite runs only through the shared build agent. It uses normal editor
preparation hooks (unattended mode suppresses them), a reentrancy guard around its
Slate callback, proper GameplayTag import/library APIs, and a result receipt with
bounded timeout. Initial harness-only failures were corrected and replaced by the
successful result above. The previously noted Sprint identity blocker is fixed.

Final current-tree regression rogue-actions-regression-verified-20261102:
build PASS (213s, including a concurrent NetCore source update), full Foundation
PASS failures=0 (48s), RogueInteractionPIE PASS (29s), RogueProjectilePIE PASS (116s),
both automation reports 1 success / 0 warnings / 0 errors; DAS_SUITES=PASS.
The remaining linear map inventory assertion was updated from 56 to 58 after
verifying the two snapshot Class get/with registrations. It remains an exact
count assertion, not a relaxed bound. This supersedes all earlier Foundation
manifest/inventory failure notes. Final tested DLLs installed using the matching
actual engine BuildId; no editor was launched outside the shared build agent.


## Projectile attack action — 2026-11-02

All runs went through the shared C:/src/DasForUE2 build-agent queue.

- `rogue-attack-v4-20261102`: build and rogue-actions PASS (10 check groups).
  Strong action ownership, factory hierarchy checks, costs, cooldown, per-owner
  Sprint, stun and death remain valid after granting the new primary attack.
- `rogue-class-archive-20261102`: class-archive PASS, 134 s. Create/remove/reopen/
  restore/reopen of saved assets preserves ActorClass, subclass and null overrides;
  ArchivePIE also passes retirement/restoration/rollback with no test warnings.
- `rogue-attack-final-regressions-20261102`: Foundation PASS (39 s), interaction
  PASS (35 s). The old projectile fixture initially checked the same frame as
  input dispatch; it now waits up to one second for the separate timer callback.
- `rogue-attack-v7-20261102`: build PASS; projectile PASS (41 s, one successful
  automation test, no warnings); projectile-attack PASS (65 s, seven check groups).
  Actual default windup measured **0.2000000104 game seconds**. Verified cooldown,
  held input, restart, stun/removal/death cancellation and attached cast Niagara.
  Sound and montage reflected calls execute without a runtime error. Audio is
  disabled in the harness; the cone mesh has no AnimInstance, so visual montage
  playback is not covered. Cast effect/sound test assets are shipped with Unreal.

The normal-editor harness uses benchmark mode with a 60 Hz fixed game step;
hidden editor windows otherwise throttle to 3 fps. Physics regressions use a
staged 0.01 s cast, no cooldown and a flat DefaultPawn muzzle; production source
remains at 0.2 s / 0.5 s / 40 cm. No native attack gameplay was added.

Receipts: Saved/Tests/rogue_actions_pie.json and
Saved/Tests/rogue_projectile_attack_pie.json. The latter has passed=true and seven
check groups. All 73 loaded DSL scripts compiled successfully. The harness
removes its probe actor, saves editor assets and closes its editor process.


## Local course presentation — 2026-11-02

Shared-agent job rogue-presentation-v11-20261102: build PASS; presentation PASS,
eight check groups, 87 s editor run. Verified Manny mesh/AnimInstance and muzzle
socket; movement through the generated graph; active attack montage and attached
course Niagara; projectile Niagara/audio/impact profile; explicit fallback and
absent-profile fallback; cast cancellation; death montage in a compatible slot.
The harness disables audio, so audible playback was not assessed.

The initial animation load assertion was caused by disabled AnimationData and
ControlRig plugins. Both are enabled, and preparation checks their classes before
loading external animation assets. Test startup waits for the editor's initial
DSL compile before PIE, preventing compilation during script callbacks.

All selected external files are gitignored. Public candidate Blueprint/map files
were checked for external serialized paths, allowing only the optional profile
path string; the presentation regression also checks hard package dependencies.


Final job rogue-presentation-final-20261102: build PASS; presentation PASS (72 s,
eight groups), including AssetRegistry hard-package dependency audit of all
/Game/DasRogue assets against excluded external roots. All 80 DSL scripts compiled
successfully. No external package is required by a public gameplay asset.

Job rogue-assets-regressions-20261102: Foundation PASS (41 s); interaction PASS
(37 s); projectile PASS (42 s); actions PASS (75 s, ten groups); projectile-attack
PASS (76 s, seven groups). Both editor harnesses closed their editor processes.


## Timed action effects — 2026-11-02

Real-PIE effects receipt has passed=true. Check groups:
- {"effect_auto_starts_and_survives_gc": true}
- {"one_instance_stacking": true, "duration_refreshed": true, "stack_scaled_ticks": 8, "expiry_removes_effect": true}
- {"no_refresh_option": true, "final_boundary_tick_once": true}
- {"manual_remove_no_recursion": true, "cancelled_timer_quiet": true, "removed_effect_collected": true}
- {"stun_cancels_and_blocks_actions": true, "natural_expiry_restores_actions": true}
- {"death_cleans_mutating_effect_array": true, "disabled_owner_rejects_grants": true, "endplay_cancels_effect_timers": true}

Shared-agent validation jobs: rogue-effects-v12-20261102, rogue-effects-migration-v3-20261102, rogue-effects-final-regressions-20261102.

## Overwhelm / hit effects — 2026-11-02

Shared-agent rogue-overwhelm-v5-20261102: build PASS; real PIE PASS (87 s,
seven groups), with runtime/timer/teardown errors treated as failures after the
editor closes. Real projectile collisions verify damage accumulation, healing
ignored, visible threshold stun, no refresh from damage while stunned, expiration
of the damage window, unsubscribe/GC/regrant without duplicate callbacks, direct
on-hit stacking including zero-damage hits, invalid-class rejection, targets
without ActionSystem, and lethal-hit cleanup.

rogue-overwhelm-migration-20261102: generic-parents PASS (21 s). A saved generic
consumer has two package exports (Blueprint and cooked contract), refers to a
script Actor class and preserves its class value through additive Actor migration.

rogue-overwhelm-regressions-20261102: Foundation, interaction, projectile,
actions (10 groups), projectile-attack (7 groups) and effects (6 groups) PASS.
The subsequent teardown fix has a final actions/attack/effects run recorded
separately. Actor status bindings now use managed subscriptions; stopping the
world no longer queries gameplay time for inactive hosts. Audio is disabled in
the harness; audible playback was not assessed.


Final rogue-overwhelm-final-20261102: actions PASS (78 s, ten groups),
projectile-attack PASS (115 s, seven groups), effects PASS (84 s, six groups).
The harness rejects runtime/timer/teardown errors after each editor closes.

## Point impacts — 2026-11-02

Shared-agent job `rogue-point-instanced-v1-20261102`: build PASS; owned-objects
PASS (16 s); generic-parents PASS (16 s), including an ordinary ScriptObject
ActorComponent reference with UE's implicit InstancedReference flag. The owner
validator still checks explicit instancing and the actual reflected field type.

Real-PIE Overwhelm PASS (58 s, seven groups); point-impact PASS (55 s, three groups):
point damage and general health damage each delivered once, hit component/location/
direction and instigator controller preserved, simulating body receives impulse,
zero-impulse body remains still, zero-damage impact consumes the projectile, and
static target produces no physics error. Logs are checked after editor shutdown
for runtime/timer/teardown failures. All 88 scripts compile successfully.

The impact interface was migrated jointly with twelve dependent Blueprints after
applying new settings separately to the magic projectile and its demo subclass.
Existing Blueprint resources were retained. The temporary migration source views
were restored and removed from the normal preparation path after the upgrade.

Hearing noise is dispatched through UE's native API without runtime errors, but
there is no hearing listener in this test; AI perception behavior and audible
playback were not assessed. External resource audit: all 135 selected licensed
files remain excluded; public candidates have no forbidden hard resource paths.

Final `rogue-point-final-regressions-20261102`: Foundation PASS (36 s), interaction
PASS (31 s), projectile PASS (31 s), projectile-attack PASS (50 s, seven groups),
effects PASS (50 s, six groups). All editor processes exited and the strict
post-exit runtime/timer checks remained clean.

## Typed calls - 2026-11-02

Manual call-frame blocks were removed from every production Content/Das/Scripts
file, including action-host helpers. The wrapper emits interface member methods,
automatically packs CollisionHit and handles checked native-view/class arguments.
No serialized Blueprint signature/default changes were required for this cleanup.

Shared-agent typed-interface-v4-20261102: 36 compiler/runtime checks PASS.
typed-interface-port-v6-20261102: presentation PASS (35 s, eight groups), effects
PASS (34 s, six groups), point impact PASS (33 s, three groups). Native tick,
Mesh/AnimInstance, class inheritance, gameplay-tag interfaces and hit payloads
execute through typed calls. Strict post-exit runtime checks remain clean.

typed-calls-final-20261102: Foundation, generic parents, native catalogue freshness,
interface contracts, interaction, projectile attack and Overwhelm PASS. Parallel
LINQ/formatting edits in the working tree were preserved and were not part of
the typed-call source change.

## Generic argument macro - 2026-11-02

DasForUE's point-damage helper now packs CollisionHit with ue_arg(call,"Hit",hit).
The specialized ue_arg_collision_hit function was deleted without an alias.
generic-ue-arg-v3-20261102: compiler/runtime macro checks PASS (47); real-PIE point
impact PASS (59 s, three groups). generic-ue-arg-final-20261102: Foundation PASS
(20 s), projectile attack PASS (55 s, seven groups), Overwhelm PASS (58 s, seven
groups). Runtime/timer/teardown log checks remain clean after editor exit.

## Declarative input macro (2026-11-02)

Shared-agent job `input-macro-v2-20261102`: PASS. Wrapper macro suite: 58 checks (11 new input cases); real-PIE interaction PASS, actions PASS (10 groups), projectile attack PASS (7 groups). Covers annotation expansion/rejection, mapped E/LMB and Shift sprint with existing teardown handling.

## Reference declaration macros (2026-11-02)

Shared-agent job `reference-macro-v1-20261102`: PASS. Macro suite: 70 checks, including 12 new reference cases. Real-PIE interaction PASS, projectile attack PASS (7 groups), point impact PASS (3 groups). Covers generated aliases, source/property/signature normalization, identity rejection, interface dispatch and the migrated gameplay reference modules.
