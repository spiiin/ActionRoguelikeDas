options gen2
module rogue_action_effect_stun public
require rogue_tags public
require rogue_action_effect public
require rogue_presentation public
require ue_api_world public
require ue_projectile_components public

[ue_class(module_id="rogue", Blueprintable)]
class RogueActionEffectStun : RogueActionEffect {

    state = ue_properties(BlueprintReadWrite) {
        var StunnedSound : AudioComponentRef
        var ActiveSoundMix : RogueSoundMixRef
    }

    defaults = ue_defaults() {
        self.DisplayName = "Stunned"
        self.Duration = 2.5f
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override Setup() : void {
        Super.Setup()
        var tags = self.GrantTags
        ue_tags_add(tags, rogue_tag_stunned())
        self.GrantTags = tags
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StartAction() : void {
        Super.StartAction()
        let owner = ue_ref(type<ActorRef>, ue_component_owner(self.Host.handle))
        let player = ue_static(GameplayStatics.GetPlayerPawn, 0)
        if (!ue_same_object(owner, player)) { return }
        rogue_load_presentation() |> if_some() $(profile : RoguePresentationProfileRef) {
            if (ue_is_valid(profile.StunSound)) {
                self.StunnedSound = ue_ref(type<AudioComponentRef>, ue_sound_spawn_2d(profile.StunSound))
            }
            if (ue_is_valid(profile.StunMix)) {
                self.ActiveSoundMix = profile.StunMix
                let mix = ue_ref(type<ue_api_world::SoundMix>, self.ActiveSoundMix.handle)
                ue_static(GameplayStatics.PushSoundMixModifier, mix)
            }
        }
    }

    [ue_function(BlueprintCallable, BlueprintEvent)]
    def override StopAction() : void {
        if (ue_is_valid(self.StunnedSound)) { ue_audio_trigger(self.StunnedSound, "EffectFinished") }
        if (ue_is_valid(self.ActiveSoundMix)) {
            let mix = ue_ref(type<ue_api_world::SoundMix>, self.ActiveSoundMix.handle)
            ue_static(GameplayStatics.PopSoundMixModifier, mix)
        }
        self.StunnedSound = default<AudioComponentRef>
        self.ActiveSoundMix = default<RogueSoundMixRef>
        Super.StopAction()
    }
}
