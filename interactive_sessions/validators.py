class InteractiveSessionValidator:
    @staticmethod
    def validate_participant_belongs_to_session(first_participant, second_participant, user):
        if first_participant not in user.get_all_participant_profiles() or second_participant not in user.get_all_participant_profiles():
            raise ValueError("The participant profile is not part of the interactive session.")
        
    @staticmethod
    def time_slot_belongs_to_trainer_and_available(time_slot, trainer):
        if time_slot.trainer != trainer or not time_slot.is_available:
            raise ValueError("The time slot does not belong to the specified trainer or is not available.")