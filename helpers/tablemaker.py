from typing import Any, Optional, Union

def league_tables(standings):
    table = []
    for team_pos in standings: 
        if "🏆" in team_pos['team']:
            row = [team_pos['rank'], team_pos['team'].replace(" - 🏆", ""), team_pos['points']]
        else:
            row = [team_pos['rank'], team_pos['team'], team_pos['points']]
        table.append(row)
    # adjust_subcolumn(table, 1, aligns=[">", "<"])
    labels = ["Rank", "Team", "Points"]
    return make_table(table, labels)

def make_table(rows: list[list[Any]], labels: Optional[list[Any]] = None, centered: bool = False) -> str:
    columns = zip(*rows) if labels is None else zip(*rows, labels)
    column_widths = _get_column_widths(columns)
    align = "^" if centered else "<"
    align = [align for _ in column_widths]

    lines = [_make_solid_line(column_widths, "╭", "┬", "╮")]

    data_left = "│ "
    data_middle = " │ "
    data_right = " │"

    if labels is not None:
        lines.append(_make_data_line(column_widths, labels, data_left, data_middle, data_right, align))
        lines.append(_make_solid_line(column_widths, "├", "┼", "┤"))
    for row in rows:
        lines.append(_make_data_line(column_widths, row, data_left, data_middle, data_right, align))
    lines.append(_make_solid_line(column_widths, "╰", "┴", "╯"))
    return "\n".join(lines)



def _get_column_widths(columns) -> list[int]:
    return [max(len(str(value)) for value in column) for column in columns]


def _make_data_line(
    column_widths: list[int],
    line: list[Any],
    left_char: str,
    middle_char: str,
    right_char: str,
    aligns: Union[list[str], str] = "<",
) -> str:
    if isinstance(aligns, str):
        aligns = [aligns for _ in column_widths]

    line = (f"{str(value): {align}{width}}" for width, align, value in zip(column_widths, aligns, line))
    return f"{left_char}{f'{middle_char}'.join(line)}{right_char}"


def _make_solid_line(
    column_widths: list[int],
    left_char: str,
    middle_char: str,
    right_char: str,
) -> str:
    return f"{left_char}{middle_char.join('─' * (width + 2) for width in column_widths)}{right_char}"

def adjust_subcolumn(
    rows: list[list[Any]], column_index: int, separator: str = "/", aligns: Union[list[str],str] = "<"
) -> None:
    column = list(zip(*rows))[column_index]
    subcolumn_widths = _get_column_widths(zip(*column))
    if isinstance(aligns, str):
        aligns = [aligns for _ in subcolumn_widths]
    
    column = [_make_data_line(subcolumn_widths, row, "", separator, "", aligns) for row in column]
    for row, new_item in zip(rows, column):
        row[column_index] = new_item