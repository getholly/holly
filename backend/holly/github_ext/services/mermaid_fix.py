def extract_valid_mermaid(text: str) -> str:
    """
    Extracts valid Mermaid diagram content from text by:
    1. Finding a valid starting keyword
    2. Detecting logical endpoints or the next Mermaid diagram

    Args:
        text: Input text potentially containing Mermaid diagram code

    Returns:
        str: Extracted valid Mermaid diagram, or empty string if none found
    """
    # List of valid Mermaid starting keywords
    valid_keywords = [
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "stateDiagram-v2",
        "erDiagram",
        "gantt",
        "pie",
        "journey",
        "gitGraph",
        "timeline",
        "mindmap",
        "quadrantChart",
        "requirement",
        "requirementDiagram",
        "C4Context",
        "C4Container",
        "C4Component",
        "C4Dynamic",
        "C4Deployment",
    ]

    # Split text into lines and process
    lines = text.split("\n")
    start_index = -1
    end_index = -1

    # Find the first line that starts with a valid keyword
    for i, line in enumerate(lines):
        trimmed = line.strip()
        if any(trimmed.startswith(keyword) for keyword in valid_keywords):
            start_index = i
            break

    # If no valid start found, return empty string
    if start_index < 0:
        return ""

    # Search for logical end of the diagram
    for i in range(start_index + 1, len(lines)):
        line = lines[i].strip()

        # Cases for ending a diagram:
        # 1. Empty line followed by non-diagram content
        # 2. Line starting with a new valid keyword (indicating a new diagram)
        # 3. Markdown code block ending (```)
        # 4. HTML comment ending (-->)

        if line in ("```", "-->", "%%") or line.startswith("<!-- "):
            end_index = i
            break

        # Check if we've reached a new diagram start
        if any(line.startswith(keyword) for keyword in valid_keywords) and i > start_index + 1:
            end_index = i - 1  # End before the new diagram starts
            break

        # Check for empty line followed by non-diagram content
        if not line and i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            # If next line doesn't look like Mermaid syntax, end here
            if next_line and not any(char in next_line for char in "[]{}()->::|&"):
                end_index = i
                break

    # If no end detected, assume it's the end of the text
    if end_index < 0:
        end_index = len(lines)

    # Extract and return the diagram
    return "\n".join(lines[start_index:end_index])


def fix_mermaid_errors(mermaid_text: str) -> str:
    return _fix_mermaid_errors(extract_valid_mermaid(mermaid_text))


def _fix_mermaid_errors(mermaid_text: str) -> str:
    """
    Check for and fix common errors in Mermaid markdown.

    Args:
        mermaid_text (str): The Mermaid markdown text to check and fix

    Returns:
        str: The fixed Mermaid markdown text
    """
    # Split into lines for easier processing
    lines = mermaid_text.strip().split("\n")
    fixed_lines = []

    # Track node names to find and fix issues with special characters
    node_names = {}

    # Fix common issues line by line
    for line in lines:
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue

        # Fix node descriptions without quotes
        if "-->" in line or "---" in line or "-.->" in line or "-..-" in line or "==>" in line:
            parts = []
            current = ""
            in_bracket = False
            bracket_type = None

            # Parse the line character by character to handle brackets correctly
            for char in line:
                current += char

                # Track bracket opening
                if not in_bracket and char in ["[", "(", "{"]:
                    in_bracket = True
                    bracket_type = char
                    bracket_close_map = {"[": "]", "(": ")", "{": "}"}

                # Handle bracket closing
                elif in_bracket and char == bracket_close_map.get(bracket_type):
                    # Check if we need to add quotes
                    bracket_content = current.split(bracket_type, 1)[1].rsplit(char, 1)[0]

                    # If content doesn't already have quotes and contains text that should be quoted
                    if (
                        not (bracket_content.startswith('"') and bracket_content.endswith('"'))
                        and not (bracket_content.startswith("'") and bracket_content.endswith("'"))
                        and any(c.isalpha() or c.isdigit() or c in "(),%:;/ " for c in bracket_content)
                    ):
                        # Replace the bracket content with quoted version
                        # Remove the closing bracket first
                        current = current[:-1]
                        # Replace the content
                        replacement = f'{bracket_type}"{bracket_content}"{char}'
                        current = current.rsplit(bracket_type, 1)[0] + replacement

                    in_bracket = False
                    bracket_type = None
                    parts.append(current)
                    current = ""

            if current:  # Add any remaining part
                parts.append(current)

            line = "".join(parts)

        # Replace problematic characters in node IDs
        if "((" in line and "))" in line:
            # Extract node name
            node_match = line.split("((", 1)[1].split("))", 1)[0]
            if "+" in node_match or "." in node_match:
                safe_name = node_match.replace("+", "Plus").replace(".", "Dot")
                node_names[node_match] = safe_name
                line = line.replace(f"(({node_match}))", f"(({safe_name}))")

        # Fix click directive
        if line.strip().startswith("click "):
            parts = line.strip().split()
            if len(parts) >= 3:
                node_id = parts[1]
                # Ensure proper formatting for click directive
                if len(parts) == 3 and '"' not in parts[2]:
                    line = f'    click {node_id} "{parts[2]}"'

        # Fix style directive used as a node
        if "style " in line and "((" in line:
            # This is likely using style incorrectly as a node
            style_name = line.split("style ", 1)[1].split("((", 1)[0].strip()
            style_label = line.split("((", 1)[1].split("))", 1)[0]
            line = f"    {style_name}(({style_label}))"

        # Fix direction directives
        if "direction" in line and not line.strip().startswith("direction"):
            line = f"    direction {line.split('direction', 1)[1].strip()}"

        fixed_lines.append(line)

    # Second pass to update references to renamed nodes
    for i, line in enumerate(fixed_lines):
        for old_name, new_name in node_names.items():
            # Update node references in connections and class assignments
            pattern = f" {old_name} "
            if pattern in line:
                fixed_lines[i] = line.replace(pattern, f" {new_name} ")

            # Fix class assignments
            if "class " in line and old_name in line:
                fixed_lines[i] = line.replace(old_name, new_name)

    # Check if flowchart or graph type is specified at the beginning
    if not any(line.strip().startswith(("flowchart ", "graph ")) for line in fixed_lines):
        fixed_lines.insert(0, "flowchart TB")

    return "\n".join(fixed_lines)


def fix_mermaid_markdown(markdown_text: str) -> str:
    """
    Fix Mermaid markdown within a larger markdown document.

    Args:
        markdown_text (str): The markdown text containing Mermaid code blocks

    Returns:
        str: The fixed markdown text
    """
    # Check if we have mermaid fenced code blocks
    if "```mermaid" not in markdown_text:
        # Try to find any mermaid content without proper code fences
        lines = markdown_text.strip().split("\n")
        if any(line.strip().startswith(("flowchart ", "graph ", "sequenceDiagram", "classDiagram")) for line in lines):
            # It's likely a bare mermaid diagram, so add fences
            return f"```mermaid\n{fix_mermaid_errors(markdown_text)}\n```"
        return markdown_text

    # Split by mermaid code blocks
    parts = []
    is_in_mermaid_block = False
    current_mermaid_block = []
    current_text = []

    for line in markdown_text.split("\n"):
        if line.strip() == "```mermaid":
            # Start of mermaid block
            if current_text:
                parts.append("\n".join(current_text))
                current_text = []
            is_in_mermaid_block = True
            current_mermaid_block = []
            parts.append("```mermaid")
        elif line.strip() == "```" and is_in_mermaid_block:
            # End of mermaid block
            fixed_mermaid = fix_mermaid_errors("\n".join(current_mermaid_block))
            parts.append(fixed_mermaid)
            parts.append("```")
            is_in_mermaid_block = False
            current_mermaid_block = []
        elif is_in_mermaid_block:
            # Inside mermaid block
            current_mermaid_block.append(line)
        else:
            # Outside mermaid block
            current_text.append(line)

    # Add any remaining text
    if current_text:
        parts.append("\n".join(current_text))

    return "\n".join(parts)


# Example usage
if __name__ == "__main__":
    # Test the new quoting functionality
    examples = [
        "A --> B[jump()]",
        "B --> C{Event Listeners Click, Keydown}",
        'C --> D[Already "quoted"]',
        'D --> E["Already quoted alternative"]',
        "E --> F((Round node))",
        "F --> G>Asymmetric]",
        "G --> H{{Hexagon}}",
    ]

    print("Testing node description quoting:\n")  # noqa: T201
    for example in examples:
        fixed = fix_mermaid_errors(example)
        print(f"Original: {example}")  # noqa: T201
        print(f"Fixed:    {fixed}\n")  # noqa: T201

    # Full example from earlier
    print("Testing complete diagram:\n")  # noqa: T201
    example_mermaid = """
    flowchart TB
        subgraph Frontend [Svelte Frontend]
            direction TB
            +page.svelte((+page.svelte)) --> app.html((app.html))
            app.html --> app.css((app.css))
            style tailwind((Tailwind Styles))
            app.css --> style
            click jump "Jump Action"
            +page.svelte --> jump
            canvas((Canvas))
            +page.svelte --> canvas
            subgraph GameLogic [Game Logic]
                direction TB
                update((update))
                draw((draw))
                getRandomHeight((getRandomHeight))
                startGame((startGame))
                jump((jump))
            end
            +page.svelte --> GameLogic
        end
        subgraph Frontend [Frontend - Svelte]
            direction TB
            A[+page.svelte] --> B{Game Logic}
            B --> C{"Event Listeners Click, Keydown"}
            C --> D[jump()]
            D --> E["draw()"]
            B --> F[update()]
            F --> G{Collision Detection}
            G --> H{gameOver = true}
            F --> I{Score Update}
            A --> J[+layout.svelte]
            J --> K[app.css]
            style A fill:#ccf,stroke:#333,stroke-width:2px
            style B fill:#ccf,stroke:#333,stroke-width:2px
            style C fill:#ccf,stroke:#333,stroke-width:2px
            style D fill:#ccf,stroke:#333,stroke-width:2px
            style E fill:#ccf,stroke:#333,stroke-width:2px
            style F fill:#ccf,stroke:#333,stroke-width:2px
            style G fill:#ccf,stroke:#333,stroke-width:2px
            style H fill:#ccf,stroke:#333,stroke-width:2px
            style I fill:#ccf,stroke:#333,stroke-width:2px
            style J fill:#ccf,stroke:#333,stroke-width:2px
            style K fill:#ccf,stroke:#333,stroke-width:2px
        end
    """

    fixed_mermaid = fix_mermaid_errors(f"blurb\n{example_mermaid}\n\n**ending**")
    print(fixed_mermaid)  # noqa: T201
