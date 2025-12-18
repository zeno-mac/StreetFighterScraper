function loadConfigFromProperties() {
  const props = PropertiesService.getScriptProperties().getProperties();
  return {
    sheetName: props.SHEET_NAME || 'Data',
  };
}

function setScriptProperties() {
  const props = PropertiesService.getScriptProperties();
  props.setProperties({
    SHEET_NAME: 'Data'
  }, true);
}

function makeHeader(sheet, object) {
  let newKeys = false
  let headers = {
    arr: [],
    safeGet(name) {
      let index = this.arr.indexOf(name);
      if (index !== -1) {
        return index;
      }
      else {
        let l = this.arr.length
        this.arr.push(name)
        newKeys = true
        return l
      }
    },
    init(names) {
      let isBlank = (names.length == 1 && names[0] == [""])
      if (isBlank) {
        names = []
      }
      this.arr = names
    }

  }

  let col = Math.max(1, sheet.getLastColumn());
  let values = sheet.getRange(1, 1, 1, col).getValues()[0]

  headers.init(values)

  for (key in object) {
    headers.safeGet(key)
  }
  if (newKeys) {
    sheet.getRange(1, 1, 1, headers.arr.length).setValues([headers.arr])
  }
  return headers

}
function fillContent(data) {
  const config = loadConfigFromProperties()
  const content = JSON.parse(data)
  const SpreadSheet_ID = SpreadsheetApp.getActiveSpreadsheet()
  let sheet = SpreadSheet_ID.getSheetByName(config.sheetName)
  headers = makeHeader(sheet, content[0])
  let row = Math.max(2, sheet.getLastRow() - 1)
  let keys = sheet.getRange(2, headers.safeGet("Id") + 1, row, 1).getValues()
  str = ""
  let existingIds = new Set()
  let rowsToAdd = new Array()
  row = Math.max(2, row + 1)
  let startingHeaders = headers.arr.length
  for (i = 0; i < keys.length; i++) {
    existingIds.add(keys[i][0])
  }
  content.forEach((match) => {
    if (existingIds.has(match["Id"])) {
      return;
    }
    let newRow = new Array(headers.arr.length).fill("")
    for (k in match) {
      col = headers.safeGet(k)
      newRow[col] = match[k]
      existingIds.add(match["id"])
    }
    rowsToAdd.push(newRow)
  })
  let lastRow = sheet.getLastRow()
  if (startingHeaders != headers.arr.length) {
    for (let i = 0; i < rowsToAdd.length; i++) {
      while (rowsToAdd[i].length < headers.arr.length) {
        rowsToAdd[i].push("")
      }
    }
  }
  if (rowsToAdd.length >= 1) {
    sheet.getRange(lastRow + 1, 1, rowsToAdd.length, headers.arr.length).setValues(rowsToAdd)
  }
  let sortColIndex = headers.arr.indexOf("Uploaded At") + 1;
  sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).sort({ column: sortColIndex, ascending: true });
}

function doPost(e) {
  try {
    fillContent(e.postData.contents)
    return ContentService.createTextOutput("ok").setMimeType(ContentService.MimeType.TEXT);
  }
  catch (error) {
    return ContentService.createTextOutput("GAS Error: "+error.message).setMimeType(ContentService.MimeType.TEXT);
  }
}
