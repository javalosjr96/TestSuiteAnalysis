function onOpen(e) {
    const sheet = SpreadsheetApp.getActiveSheet();
    resizeCells(sheet)
    boldFirstColumnRowsByName(sheet)
    addProductTeams(sheet)
    addPriorities(sheet)
}

function resizeCells(sheet) {
    const dataRange = sheet.getDataRange();
    const startingRow = dataRange.getRow();
    const endingRow = startingRow + dataRange.getNumRows() - 1;
    for (let i = startingRow; i < endingRow + 1; i++) {
        sheet.setRowHeightsForced(i, 1, 21)
    }
    sheet.setColumnWidth(1,330);
    sheet.setColumnWidth(2,125);
    sheet.setColumnWidth(3,180);
    sheet.setColumnWidth(4,115);
}

function boldFirstColumnRowsByName(sheet) {
    const columnNames=["Pull Request:","Name","Jira Tickets"]

    const dataRange = sheet.getRange(1, 1, sheet.getLastRow(), 1);
    const values = dataRange.getValues();
    for (let b = 0; b < columnNames.length; b++) {
        for (let i = 0; i < values.length; i++) {
            if (values[i][0] === columnNames[b]) {
                const rowNumber = i + 1
                console.log(rowNumber);
                boldRow(sheet,rowNumber);
            }
        }
    }

}

function addProductTeams(sheet) {

    const cell = findCellByNameAndColumn("Product Team",4,sheet)

    const productTeams = ["Frontend Infrastructure", "Business Process Management", "Content Management", "Echo", "App Security", "Search", "Commerce", "Database Infrastructure", "Platform Experience", "Core Infrastructure", "Headless"];
    const rule = SpreadsheetApp
        .newDataValidation()
        .requireValueInList(productTeams, true)
        .setAllowInvalid(false)
        .build();

    cell.setDataValidation(rule);

}

function addPriorities(sheet) {
    const cell = findCellByNameAndColumn("Priority",5,sheet)

    const priorities = ['1','2','3','4','5'];

    const rule = SpreadsheetApp
        .newDataValidation()
        .requireValueInList(priorities, true)
        .setAllowInvalid(false)
        .build();

    cell.setDataValidation(rule);

}

function findCellByNameAndColumn(cellValue,columnNumber,sheet){

    const dataRange = sheet.getRange(1, columnNumber, sheet.getLastRow(), 1);

    const values = dataRange.getValues();

    var rowNumber = 0;

    for (let i = 0; i < values.length; i++) {
        if (values[i][0] === cellValue) {
            rowNumber = i + 2

            return sheet.getRange(rowNumber, columnNumber)
        }
    }

    return 0
}

function boldRow(sheet, rowIndex) {
    const rowRange = sheet.getRange(rowIndex, 1, 1, sheet.getLastColumn()); // Adjust columns if needed
    rowRange.setFontWeight("bold");
}


