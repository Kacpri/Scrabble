def paint_graphic_item(graphic_item, pen=None, brush=None):
    if pen:
        graphic_item.setPen(pen)

    if brush:
        graphic_item.setBrush(brush)

    graphic_item.update()


def paint_graphic_items(graphic_items, pen=None, brush=None):
    if graphic_items:
        for graphic_item in graphic_items:
            paint_graphic_item(graphic_item, pen, brush)


def algebraic_notation_to_coords(algebraic_notation):
    x = ord(algebraic_notation[0]) - ord('A')
    y = int(algebraic_notation[1:]) - 1
    return f"{x}-{y}"


def algebraic_notations_to_coords(algebraic_notations):
    coords = []
    for notation in algebraic_notations:
        coords.append(algebraic_notation_to_coords(notation))
    return coords


def is_coords_of_rack(coords):
    x, y = coords.split('-')
    x, y = int(x), int(y)
    return y == 16 and 3 < x < 12


def split_coords(coords):
    x, y = coords.split('-')
    return int(x), int(y)


def coords_above(coords):
    x, y = split_coords(coords)
    return f'{x}-{y - 1}'


def coords_below(coords):
    x, y = split_coords(coords)
    return f'{x}-{y + 1}'


def coords_on_right(coords):
    x, y = split_coords(coords)
    return f'{x + 1}-{y}'


def coords_on_left(coords):
    x, y = split_coords(coords)
    return f'{x - 1}-{y}'


def tile_above(coords, tiles_dict):
    return tiles_dict.get(coords_above(coords))


def tile_below(coords, tiles_dict):
    return tiles_dict.get(coords_below(coords))


def tile_on_right(coords, tiles_dict):
    return tiles_dict.get(coords_on_right(coords))


def tile_on_left(coords, tiles_dict):
    return tiles_dict.get(coords_on_left(coords))


triple_word_bonus_positions = ['A1', 'A8', 'A15', 'H1', 'H15', 'O1', 'O8', 'O15']
triple_word_bonus_coords = algebraic_notations_to_coords(triple_word_bonus_positions)

double_word_bonus_positions = ['B2', 'C3', 'D4', 'E5', 'N2', 'M3', 'L4', 'K5', 'B14', 'C13', 'D12', 'E11',
                               'N14', 'M13', 'L12', 'K11', 'H8']
double_word_bonus_coords = algebraic_notations_to_coords(double_word_bonus_positions)

triple_letter_bonus_positions = ['F2', 'J2', 'F6', 'J6', 'B6', 'N6', 'F10', 'J10', 'B10', 'N10', 'F14', 'J14']
triple_letter_bonus_coords = algebraic_notations_to_coords(triple_letter_bonus_positions)

double_letter_bonus_positions = ['D1', 'L1', 'G3', 'I3', 'H4', 'A4', 'O4', 'C7', 'D8', 'C9', 'G7', 'G9', 'I7',
                                 'I9', 'M7', 'M9', 'L8', 'A12', 'H12', 'O12', 'G13', 'I13', 'D15', 'L15']
double_letter_bonus_coords = algebraic_notations_to_coords(double_letter_bonus_positions)
