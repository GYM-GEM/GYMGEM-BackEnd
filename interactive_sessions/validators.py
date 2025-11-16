class InteractiveSessionValidator:
    @staticmethod
    def validate_participant_belongs_to_session(first_participant, second_participant, user):
        if first_participant not in user.get_all_participant_profiles() or second_participant not in user.get_all_participant_profiles():
            raise ValueError("The participant profile is not part of the interactive session.")