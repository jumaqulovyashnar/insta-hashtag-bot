def calculate_coins_earned(referral_count: int, coins_per_referral: int) -> int:
    """
    Pure function - calculate total coins earned.
    """
    return referral_count * coins_per_referral

def has_unlocked_vip(total_coins: int, threshold: int) -> bool:
    """
    Check if the user is eligible for VIP access based on their coin balance.
    """
    return total_coins >= threshold

def coins_remaining_for_vip(total_coins: int, threshold: int) -> int:
    """
    Calculate remaining coins needed to reach the VIP threshold.
    """
    remaining = threshold - total_coins
    return max(remaining, 0)
