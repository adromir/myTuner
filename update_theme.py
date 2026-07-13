import re
import json

base_html_path = 'e:/myTuner/app/templates/base.html'

with open(base_html_path, 'r', encoding='utf-8') as f:
    content = f.read()

light_colors = {
    "background": "#fcf8ff",
    "surface": "#fcf8ff",
    "surface-bright": "#fcf8ff",
    "surface-container-lowest": "#ffffff",
    "surface-container-low": "#f5f2fe",
    "surface-container": "#efecf8",
    "surface-container-high": "#e9e6f3",
    "surface-container-highest": "#e4e1ed",
    "surface-dim": "#dbd8e4",
    "surface-variant": "#e4e1ed",
    "inverse-surface": "#303038",
    "inverse-on-surface": "#f2effb",

    "on-background": "#1b1b23",
    "on-surface": "#1b1b23",
    "on-surface-variant": "#464554",

    "primary": "#4648d4",
    "on-primary": "#ffffff",
    "primary-container": "#6063ee",
    "on-primary-container": "#fffbff",
    "inverse-primary": "#c0c1ff",
    
    "primary-fixed": "#e1e0ff",
    "on-primary-fixed": "#07006c",
    "primary-fixed-dim": "#c0c1ff",
    "on-primary-fixed-variant": "#2f2ebe",

    "secondary": "#006c49",
    "on-secondary": "#ffffff",
    "secondary-container": "#6cf8bb",
    "on-secondary-container": "#00714d",
    
    "secondary-fixed": "#6ffbbe",
    "on-secondary-fixed": "#002113",
    "secondary-fixed-dim": "#4edea3",
    "on-secondary-fixed-variant": "#005236",

    "tertiary": "#904900",
    "on-tertiary": "#ffffff",
    "tertiary-container": "#b55d00",
    "on-tertiary-container": "#fffbff",

    "tertiary-fixed": "#ffdcc5",
    "on-tertiary-fixed": "#301400",
    "tertiary-fixed-dim": "#ffb783",
    "on-tertiary-fixed-variant": "#703700",

    "error": "#ba1a1a",
    "on-error": "#ffffff",
    "error-container": "#ffdad6",
    "on-error-container": "#93000a",

    "outline": "#767586",
    "outline-variant": "#c7c4d7",
    
    "surface-tint": "#494bd6"
}

dark_colors = {
    "background": "#121217",
    "surface": "#121217",
    "surface-bright": "#38383f",
    "surface-container-lowest": "#0c0c11",
    "surface-container-low": "#1b1b21",
    "surface-container": "#1f1f25",
    "surface-container-high": "#2a2930",
    "surface-container-highest": "#34343b",
    "surface-dim": "#121217",
    "surface-variant": "#464554",
    "inverse-surface": "#e4e1ed",
    "inverse-on-surface": "#303038",

    "on-background": "#e4e1ed",
    "on-surface": "#e4e1ed",
    "on-surface-variant": "#c7c4d7",

    "primary": "#c0c1ff",
    "on-primary": "#1211a5",
    "primary-container": "#2f2ebe",
    "on-primary-container": "#e1e0ff",
    "inverse-primary": "#4648d4",

    "primary-fixed": "#e1e0ff",
    "on-primary-fixed": "#07006c",
    "primary-fixed-dim": "#c0c1ff",
    "on-primary-fixed-variant": "#2f2ebe",

    "secondary": "#4edea3",
    "on-secondary": "#003824",
    "secondary-container": "#005236",
    "on-secondary-container": "#6cf8bb",

    "secondary-fixed": "#6ffbbe",
    "on-secondary-fixed": "#002113",
    "secondary-fixed-dim": "#4edea3",
    "on-secondary-fixed-variant": "#005236",

    "tertiary": "#ffb783",
    "on-tertiary": "#4d2300",
    "tertiary-container": "#703700",
    "on-tertiary-container": "#ffdcc5",

    "tertiary-fixed": "#ffdcc5",
    "on-tertiary-fixed": "#301400",
    "tertiary-fixed-dim": "#ffb783",
    "on-tertiary-fixed-variant": "#703700",

    "error": "#ffb4ab",
    "on-error": "#690005",
    "error-container": "#93000a",
    "on-error-container": "#ffdad6",

    "outline": "#908f9f",
    "outline-variant": "#464554",

    "surface-tint": "#c0c1ff"
}

# Construct CSS block
css_lines = ["    <style id=\"theme-variables\">", "        :root {"]
for k, v in light_colors.items():
    css_lines.append(f"            --color-{k}: {v};")
css_lines.append("        }")
css_lines.append("        .dark {")
for k, v in dark_colors.items():
    css_lines.append(f"            --color-{k}: {v};")
css_lines.append("        }")
css_lines.append("        input, select, textarea {")
css_lines.append("            background-color: var(--color-surface-container-highest);")
css_lines.append("            color: var(--color-on-surface);")
css_lines.append("            border-color: var(--color-outline-variant);")
css_lines.append("        }")
css_lines.append("        input::placeholder, textarea::placeholder {")
css_lines.append("            color: var(--color-on-surface-variant);")
css_lines.append("            opacity: 0.7;")
css_lines.append("        }")
css_lines.append("    </style>")
css_block = "\n".join(css_lines)

# Inject CSS block right before </head>
if "theme-variables" not in content:
    content = content.replace("</head>", css_block + "\n</head>")

# Replace Tailwind colors block
tailwind_colors = "{\n"
for k in light_colors.keys():
    tailwind_colors += f'"{k}": "var(--color-{k})",\n'
tailwind_colors += "}"

# Regex replace the colors dictionary
content = re.sub(r'"colors":\s*\{[^}]+\}', f'"colors": {tailwind_colors}', content, flags=re.MULTILINE|re.DOTALL)

with open(base_html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected CSS variables and updated Tailwind config.")
