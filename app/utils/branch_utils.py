PREFERRED_BRANCH_ORDER = ["봉천", "인천", "홍대", "부천", "목동", "삼성"]

def get_branch_sort_key(branch):
    """
    Returns the sort index for a branch based on PREFERRED_BRANCH_ORDER.
    Accepts SQLAlchemy Branch model instance, dictionary, or string branch name.
    """
    if isinstance(branch, str):
        name = branch
    elif isinstance(branch, dict):
        name = branch.get('name', '')
    elif hasattr(branch, 'name'):
        name = getattr(branch, 'name', '') or ''
    else:
        name = str(branch)

    for idx, target in enumerate(PREFERRED_BRANCH_ORDER):
        if target in name:
            return idx
    return len(PREFERRED_BRANCH_ORDER)

def sort_branches(branches):
    """
    Sorts a list or query result of branches by PREFERRED_BRANCH_ORDER.
    """
    if branches is None:
        return []
    branch_list = list(branches)
    return sorted(branch_list, key=get_branch_sort_key)
