# Биндинг для интерфейса и сундука

Рабочий checkout интеграции: C:/src/DasForUE2-main, исходная версия f8528c7. Целевая версия движка — локальная UE 5.8.3.

| Возможность | Реализация |
| --- | --- |
| Объявить UE интерфейс полностью в daScript | ue_interface и FDasInterfaceService создают Blueprint Interface |
| Реализовать Interact без параметров | ue_implements и ue_function(BlueprintCallable) |
| Вызвать интерфейс из daScript | ue_begin_interface_call; обёртка rogue_interact соответствует сигнатуре Тома |
| Компоненты и attachment | ue_component, RootComponent, Attach создают SCS-компоненты |
| Параметры анимации | ue_properties(EditAnywhere,BlueprintReadWrite) |
| BeginPlay и Tick | Зарезервированные методы DSL на универсальном ADasActor |
| Отключение tick | ActorRef.SetActorTickEnabled через существующий native gameplay manifest |
| Collision profiles | StaticMeshComponentRef.SetCollisionProfileName; профиль Interaction объявлен в конфигурации порта |
| Константная интерполяция | Обычная daScript математика с require math |
| Поворот крышки с обновлением сцены | Добавлен ue_scene_set_relative_rotation в ue_scene_components |
| Событие завершения | ue_function(BlueprintEvent), пустая базовая реализация и override в дочернем классе |
| Наследование интерфейса | Исправлена схема адаптера: содержит собственные объявления интерфейсов, унаследованные остаются на родительском Blueprint |

## Изменения DasForUE

В ue_scene_components добавлен универсальный поворот компонента с сохранением относительных положения и масштаба. Прямое присваивание отражаемому RelativeRotation не является заменой engine scene update.

В DasAuthoring.cpp исправлено формирование owned schema для дочернего класса: повторная передача интерфейсов родителя заставляла валидатор требовать Interact как новый метод потомка. Исправление не добавляет игровую логику в C++.

Результат работы игровых классов проверяет DasForUE.Ports.RogueChest. Тестовый наблюдатель тоже написан на daScript; C++ используется только для создания тестового мира, импорта классов и проверок.

## Сопоставление с оригиналом

Имена UE классов не имеют C++ префиксов A/U/I. Вместо UInterface и IInterface создаётся один Blueprint Interface с тем же игровым контрактом Interact().

Collision и начальное отключение tick выполняются в BeginPlay, после создания компонентов. В оригинале соответствующие значения устанавливаются в C++ конструкторе. Текущий прогресс анимации хранится в отражаемом изменяемом поле DSL; настройки скорости и цели отделены от него.

Разрешение на публикацию производного кода и лицензия согласуются с автором отдельно; чужие игровые assets в проект не добавлены.


## Компонент и контроллер (2 ноября 2026)

Для sphere overlap, Actor bounds, GetPlayerViewPoint с out-параметрами, ControlRotation, typed references, component ownership и Enhanced Input использован существующий API. Математика весов и dispatch интерфейса написаны на daScript.

В DasForUE добавлен универсальный `ADasPlayerController`: нативный APlayerController с тем же lifecycle/frame bridge, что у других daScript actor hosts. DSL поддерживает базу PlayerController, компоненты SCS, defaults, retirement и восстановление lifecycle при reinstancing. Этот хост реализует IGenericTeamAgentInterface и хранит byte team ID; конкретное значение задаёт скрипт.

Добавлены `ue_player_controls_ready(PlayerControllerRef)` и `ue_controller_set_team(PlayerControllerRef,int)`. Первый проверяет локальный EnhancedPlayerInput, EnhancedInputComponent и subsystem; второй проверяет interface и диапазон 0..255. Оба используют существующие проверки ссылок и мира, операция записи также проверяет lifecycle/construction ограничения.

Скрипт повторяет попытку подключения ввода до готовности. Поддержка виртуального SetupInputComponent для этого этапа не потребовалась. В Config/DefaultInput.ini включены EnhancedPlayerInput и EnhancedInputComponent.

Отличия от исходника: Started вместо Triggered; фильтр по интерфейсу до расчёта веса; повторный поиск при нажатии; guards для отсутствующего pawn и неположительного радиуса. Нативный код не содержит поиска сундука, весов или обработчика E.


## RogueProjectile (2 ноября 2026)

Добавлены универсальные возможности интеграции:

- Шестой аргумент `ue_actor_spawn(..., owner, collision, instigator)` задаёт FActorSpawnParameters.Instigator до FinishSpawning/BeginPlay. Instigator проверяется как живой Pawn в текущем игровом мире. Старый низкоуровневый extern спавна сохранён.
- `ue_projectile_components` объявляет типы native ProjectileMovementComponent, NiagaraComponent и AudioComponent. `ue_projectile_movement_launch` настраивает UpdatedComponent, скорость, гравитацию и локальную velocity после регистрации SCS-компонентов. Численные игровые значения передаются из daScript.
- `CollisionHit` — отражаемая копия обычных полей FHitResult для многопараметрических callbacks OnComponentHit/OnProjectileBounce. Native ActorInstanceHandle не выдаётся скрипту. Координаты и нормали, время/дистанция, флаги, индексы, имена костей и ссылки Actor/Component/PhysMaterial копируются при постановке события в очередь. Применяются обычные GC/liveness проверки очереди; нечисловые значения отклоняются.
- `ue_effect_burst` вызывает world-owned, auto-destroy Niagara/audio операции. Эффекты не принадлежат уничтожаемому снаряду и продолжают работу после его EndPlay. Managed `ue_effect_play` по-прежнему останавливается с владельцем.

SphereComponent.SetSphereRadius, collision profile, IgnoreActorWhenMoving, native property Instigator, SetActorTickEnabled, InitialLifeSpan и K2_DestroyActor используют существующие биндинги. Поиск камеры, положение спавна, обработка ЛКМ и попадания, выбор эффектов и Destroy находятся в daScript.

Вместо C++ PostInitializeComponents настройка выполняется в BeginPlay, до первого movement tick. База доступна для создания в редакторе (исходный класс Abstract); в демонстрации используется дочерний RogueProjectileDemo. ProjectileClass в действии атаки хранится как ActorClass, LastProjectile как ActorRef: текущие authored references требуют точного stable ID, а демонстрационный потомок имеет собственный ID.


Collision для снаряда сверена с Config/DefaultEngine.ini исходного коммита: object channel Projectile = ECC_GameTraceChannel2 с default Ignore; профиль Projectile QueryOnly с игнорированием Visibility/Camera; BlockAll, CharacterMesh и PhysicsActor блокируют Projectile. Текущий профиль сундука сохраняет прежнюю настройку взаимодействия и дополнительно блокирует Projectile. Это позволяет проверять попадание в сундук и стену без изменения проверенного поведения E.


## Health / magic projectile

Existing bindings cover ActorComponent composition, native owner OnTakeAnyDamage
callbacks, authored multicast events, text rendering, material vector parameters,
ApplyDamage and PlayerController instigator attribution. Projectile impact uses an
explicit RogueImpactHandler interface and checked interface dispatch, avoiding
unsupported inherited managed-event overrides and preserving nested authored-call
authorization. All damage/health/target behavior is daScript.

Added generic `ue_actor_destroy_self_next_tick`: immediately destroying the damage
causer inside OnComponentHit invalidated queued OnTakeAnyDamage snapshots, dropping
the notification by design. Deferring native Destroy to the next world timer tick
preserves the existing strict callback lifetime checks and lets damage notifications
complete. No changes to program compilation/caching or VM optimization paths.


## Interface migration

DasEditor now migrates existing authored interface contracts through the same
Das.DSL.Interfaces.Apply command. Interface/consumer snapshots and typed preflight
replace the blanket structural-policy rejection. Matching DAS implementation
sources are reimported in a bounded batch; generated function and interface-event
bridges are rebuilt, preserving user CDO overrides. Connected incompatible pins,
custom defaults, hand-authored bridge branches and graph-name conflicts are
protected by refusal/rollback. This changes editor import behavior only; runtime
program-cache optimization remains in the separate worktree.


## RogueCharacter: movement/camera slice (2026-11-02)

Added canonical SpringArmComponentRef to ue_character_control.das, using the
existing checked native component/default machinery. SCS boom and CameraComponent
with AttachSocket=SpringEndpoint work without a new native host or gameplay code.
Movement basis (controller yaw), axis handlers, Jump/StopJumping and setup are
daScript. Existing CharacterMovement properties and synthesized native methods
were sufficient; no C++ or program-cache/VM optimization changes in this slice.
Native CharacterMovement subobject defaults combined with authored SCS composition
are still refused by current policy. Editable script parameters are therefore
applied to CharacterMovement in BeginPlay, after component registration.
Enhanced Input asset setup remains editor Python. Persist whole mapping array
after setting modifiers because map_key returns a struct copy in Python.


## Character combat/health/death slice (2026-11-02)

Existing ue_line_trace/ue_sphere_trace with explicit ignored actors, UETraceHit
math fields, ue_actor_spawn and native Character/PlayerController movement/input
methods suffice. Gameplay uses existing native APIs. Added Attributes and
HealthLabel to authored Character, native damage -> component multicast ->
daScript terminal death. Generic controller remains pawn-based; its muzzle
math does not require authored Character types. Legacy DefaultPawn regression
fixtures set staged MuzzleHeight=0 to retain their flat-flight physics check;
actual Character uses 40 and is covered by the combat integration test.

Cached authored programs now retain value-only method/property signature and
reference declaration descriptors and replay them inside an active compiler
scope on a cache hit. This preserves typed call/delegate generation without
importing a component module and registering its owner callbacks on an Actor.
Reference modules retain their original lightweight dependencies. Compiled code
and owner contexts remain separate; the fix does not disable program caching.

## Vector expressions in the port

All 29 gameplay/example scripts and the three Tests/Das sources were audited.
Repeated zero/one vectors and zero rotators use ue_vector_math constants. Movement,
interaction and aiming use native UE vector arithmetic and ue_rotate_vector;
ue_direction_rotation shares the camera-facing/aim-angle calculation. World
coordinates retain double precision.

ue_vector_math adds 48 readable 2/3-component selections for UEVector/UEVector2D,
14 writable selections without duplicate destinations, constants and native-math
aliases. Native arithmetic is reused, rather than reimplemented. Named literal
math constants also work in ue_defaults through safe importer syntax expansion.
Definitions, exact scope and read-modify-write examples: Docs/VectorMath.md in
DasForUE2-main. The numeric sizes/offsets chosen for the placeholder geometry stay
explicit in their defaults.
## Owned ScriptObject factory and actions

ue_object_new(type<BaseRef>, loadedClass, outer) uses native-base validation plus
CDO authored-identity hierarchy validation before NewObject. A derived authored
class can be returned as a base reference; unrelated authored siblings, Actor
classes and invalid/template/cross-world outers remain rejected. The caller must
retain a strong reflected property; an Outer or a standalone weak handle is not
ownership. RogueActionSystemComponent stores actions before invoking Setup.

RogueCharacter configures its SprintActionClass with a class default marker and
grants it from daScript BeginPlay. The generic component's DefaultActions is left
independent; only the legacy exact Python bootstrap override is migrated away.
Sprint, costs, cooldown, tags, native-interface callbacks and death cancellation
run in daScript. The new rogue-actions suite exercises this in a normal editor
process owned by the shared agent and cleans up/closes it automatically.


## Projectile attack and class retirement

The attack uses the existing managed UObject timer API; no native gameplay class
was introduced. The controller only routes input to the character's action system.
ue_animation now exposes ue_character_play_montage; ue_effects exposes
ue_niagara_spawn_attached (snap, auto-destroy) and ue_sound_play_2d. These are script
helpers over checked reflected calls, without new native externs.

Retired-field migration no longer rejects every schema containing Class fields.
Class values use the shared Read/WriteDasPropertyValue snapshot, reflected
ClassValue ownership, GC roots and reinstancing remap. Restore preflights the
declared metaclass and retained value. Scope/rollback rules remain those of the
existing archive migration. The asset regression now covers a native actor class,
a subclass override and null through remove, reopen, restore and reopen.


## Local presentation resources — 2026-11-02

Authored references now support DataAsset and PrimaryDataAsset hosts alongside
the existing UObject hosts. The character retains its presentation profile in
a reflected strong property. Generic LoadOptionalAsset resolves only valid
/Game paths, returns null quietly for absent packages, and runs on the game thread.

DasAnimationAssetLibrary builds a native UAnimInstance AnimGraph from the supplied
skeleton/blend space and montage slot. This is presentation only: movement,
actions, damage and projectile logic remain in daScript. Explicit reflected
helpers configure existing Niagara and audio components without adding externs.
AnimationData and ControlRig are enabled to deserialize the acquired animations.


## Timed effects and ScriptObject migration

Gameplay effects use existing managed UObject timers and reflected action
ownership. No native effect gameplay class was introduced. Plain ScriptObject
structural reimport updates the cooked method contract and snapshots it for
rollback. Additive changes can include independently authored referring assets;
removals, signature changes and default changes retain stricter migration guards.
Other generic native parent families still retain their structural reimport guard.
Direct cooked contract owners are repaired before identity preflight only when
the descriptor ID agrees with the stored import and requested class. Dependent
generated classes also refresh their contract owner after compilation.

ResetDuration is reflected so inherited effects invoke the owning class's timer
implementation. Existing timer APIs suffice; no runtime callback lookup changes
remain in this slice. Script-only inherited helpers containing managed callbacks
are not generalized by this change.

## Overwhelm, hit effects and additive Actor migration

Existing component queries, dynamic multicast methods and managed ue_event
subscriptions cover the gameplay slice. ClassIsChildOf is called through the
checked reflection API before GrantAction; no native gameplay helper was added.
EffectOnHit can apply without positive damage, and targets without ActionSystem
continue to receive ordinary damage.

Additive migration now permits independent authored referencers for supported
hosts when all existing declarations/defaults/metadata/implementation contracts
are unchanged. Other structural changes retain their existing scope guards.
Blueprint packages may include their owned DasScriptClassData export: collection
checks its name, type, object identity and stored authored ID before accepting it.
The rollback snapshot already captures that contract. Unknown extra exports
remain rejected, with the package and asset classes included in the diagnostic.

Target status/health subscriptions use managed ue_event lifetime. Explicit
Overwhelm subscriptions are removed before StopAction releases tags or ownership.
Inactive-host Shutdown skips gameplay time/cooldown calculation during teardown.

## Point impact bridge

The sample's interface now carries `CollisionHit` alongside the target Actor.
`ue_arg_collision_hit` writes its detached public fields into checked call frames.
`ue_apply_point_damage` invokes a small native UDasCollisionLibrary adapter which
reconstructs FHitResult and calls UGameplayStatics::ApplyPointDamage. All damage
selection, physical simulation checks, impulse magnitude and on-hit effects stay
in daScript. `ue_report_noise` supplies the current owner's world context to UE
hearing. No callback memory or actor-instance-handle internals escape the boundary.

The runtime owner validator recognizes the native DefaultToInstanced class rule;
this fixes Overwhelm's borrowed ActorComponent reference after the explicit
Instanced validation added by the owned-object work. GenericParents and real-PIE
Overwhelm cover the regression; owned-objects remains green.
