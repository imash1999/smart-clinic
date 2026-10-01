def calculate_priority(complaint):

    high_priority = [
        "болит сердце",
        "боль в груди",
        "потеря сознания"
    ]

    medium_priority = [
        "температура",
        "боль в суставах",
        "сильная боль"
    ]


    if complaint in high_priority:
        return 10

    elif complaint in medium_priority:
        return 5

    else:
        return 1
