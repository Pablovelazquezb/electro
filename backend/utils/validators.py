# backend/utils/validators.py
from datetime import datetime
from typing import Tuple, Optional

def validate_date_range(
    start_date_str: str,
    end_date_str: str,
    max_days_history: int = 365
) -> Tuple[bool, Optional[str], Optional[datetime], Optional[datetime]]:
    """
    Validate date range
    
    Returns:
        (is_valid, error_message, start_date, end_date)
    """
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(
            hour=0, minute=0, second=0
        )
    except ValueError as e:
        return False, f'Invalid date format. Use YYYY-MM-DD. Error: {str(e)}', None, None
    
    if start_date > end_date:
        return False, 'Start date must be before end date', None, None
    
    if start_date > datetime.now():
        return False, f'Start date cannot be in the future', None, None
    
    days_diff = (datetime.now() - start_date).days
    if days_diff > max_days_history:
        return False, (
            f'Start date is more than {max_days_history} days in the past. '
            'The device may not have data that old.'
        ), None, None
    
    return True, None, start_date, end_date
