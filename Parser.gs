function doPost(e) {
  const content = JSON.parse(e.postData.contents)
  const SpreadSheet_ID = SpreadsheetApp.getActiveSpreadsheet()
  let sheet = SpreadSheet_ID.getSheetByName("Data")
  pos = {
    safeGet(name) {
      if (name in this) {
        return this[name]
      }
      else {
        let l = sheet.getLastColumn() + 1
        sheet.getRange(1, l).setValue(name)
        pos[name] = l
        return l
      }
    }
  }
  let values = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0]
  for (i = 0; i < values.length; i++) {
    pos[values[i]] = i + 1
  }
  let row = sheet.getLastRow() +1
  let lastDate = sheet.getRange(row - 1, colMap["uploaded_at"]).getValue()
  str = ""
  content.forEach((match) => {
    if (Number(match["uploaded_at"]) <= lastDate) {
      return;
    }
    for (k in match) {
      col = pos.safeGet(k)
      sheet.getRange(row, col).setValue(match[k])
    }
    row++

  })
  return ContentService.createTextOutput("ok").setMimeType(ContentService.MimeType.TEXT);
}