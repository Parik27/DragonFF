material_colours = {
    (255, 60, 0, 255)  : ("Right Tail Light", ""),
    (185, 255, 0, 255) : ("Left Tail Light", ""),
    (0, 255, 200, 255) : ("Right Headlight", ""),
    (255, 175, 0, 255) : ("Left Headlight", ""),
    (0, 255, 255, 255) : ("4 Colors Paintjob", ""),
    (255, 0, 255, 255) : ("Fourth Color", ""),
    (0, 255, 255, 255) : ("Third Color", ""),
    (255, 0, 175, 255) : ("Secondary Color", ""),
    (60, 255, 0, 255)  : ("Primary Color", ""),
    (184, 255, 0, 255) : ("ImVehFT - Breaklight L", ""),
    (255, 59, 0, 255)  : ("ImVehFT - Breaklight R", ""),
    (255, 173, 0, 255) : ("ImVehFT - Revlight L", ""),
    (0, 255, 198, 255) : ("ImVehFT - Revlight R", ""),
    (255, 174, 0, 255) : ("ImVehFT - Foglight L", ""),
    (0, 255, 199, 255) : ("ImVehFT - Foglight R", ""),
    (183, 255, 0, 255) : ("ImVehFT - Indicator LF", ""),
    (255, 58, 0, 255)  : ("ImVehFT - Indicator RF", ""),
    (182, 255, 0, 255) : ("ImVehFT - Indicator LM", ""),
    (255, 57, 0, 255)  : ("ImVehFT - Indicator RM", ""),
    (181, 255, 0, 255) : ("ImVehFT - Indicator LR", ""),
    (255, 56, 0, 255)  : ("ImVehFT - Indicator RR", ""),
    (0, 16, 255, 255)  : ("ImVehFT - Light Night", ""),
    (0, 17, 255, 255)  : ("ImVehFT - Light All-day", ""),
    (0, 18, 255, 255)  : ("ImVehFT - Default Day", ""),
}

material_specular_levels = {
    0.00 : ("Off", "Disabled (0.0)"),
    0.99 : ("60", "Specular (0.99)"),
    0.87 : ("61", "Specular (0.87)"),
    0.79 : ("62", "Specular (0.79)"),
    0.69 : ("63", "Specular (0.69)"),
    0.63 : ("64", "Specular (0.63)"),
    0.56 : ("65", "Specular (0.56)"),
    0.50 : ("66", "Specular (0.50)"),
    0.44 : ("67", "Specular (0.44)"),
    0.39 : ("68", "Specular (0.39)"),
    0.34 : ("69", "Specular (0.34)"),
    0.30 : ("70", "Specular (0.30)"),
    0.26 : ("71", "Specular (0.26)"),
    0.20 : ("72", "Specular (0.20)"),
    0.19 : ("73", "Specular (0.19)"),
    0.16 : ("74", "Specular (0.16)"),
    0.14 : ("75", "Specular (0.14)"),
    0.12 : ("76", "Specular (0.12)"),
    0.09 : ("77", "Specular (0.09)"),
    0.08 : ("78", "Specular (0.08)"),
    0.06 : ("79", "Specular (0.06)"),
    0.04 : ("80", "Specular (0.04)"),
    0.03 : ("81", "Specular (0.03)"),
    0.01 : ("82", "Specular (0.01)"),
}

material_reflection_intensities = {
    0.0 : ("Off", "Reflection is disabled (0.0)"),
    **{
        round(i / 100, 2) : ("ENV %d" % i, "Reflection level %d" % i)
        for i in range(1, 51)
    },
    1.0 : ("Mirror", "Mirror effect (1.0)"),
    3.0 : ("Chrome", "Chrome surface (3.0)"),
}

material_reflection_scales = {
    0.0 : ("OFF SPEC", "Glare is disabled"),
    0.2 : ("SPEC 51", "51 Glare"),
    0.4 : ("SPEC 102", "102 Glare"),
    0.6 : ("SPEC 153", "153 Glare"),
    0.8 : ("SPEC 204", "204 Glare"),
    1.0 : ("MAX SPEC ", "255 Glare"),
}
