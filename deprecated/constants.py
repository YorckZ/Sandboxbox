def select_field(label: str, counter: int):
    inner_field: str = "dropdown_"+str(counter)
    return f"""
            <label for="{inner_field}">{label}</label>
            <select id="{inner_field}" onchange="updateDropdown11()">
                <option value="n.a.">n.a.</option>
                <option value="ja">Ja</option>
                <option value="nein">Nein</option>
                <option value="unsicher">Ich bin mir unsicher.</option>
            </select>
            <div id="dynamicArea11" style="margin-top:20px;"></div>
    """
