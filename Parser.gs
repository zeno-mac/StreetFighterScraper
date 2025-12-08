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


function fillContent(data){
  const config = loadConfigFromProperties()
  const content = JSON.parse(data)
  const SpreadSheet_ID = SpreadsheetApp.getActiveSpreadsheet()
  let sheet = SpreadSheet_ID.getSheetByName(config.sheetName)
  pos = {
    safeGet(name) {
      if (name in this) {
        console.log("Present: "+ name+", coord: "+String(this[name]))
        return this[name]
      }
      else {
        let l = sheet.getLastColumn() + 1
        sheet.getRange(1, l).setValue(name)
        pos[name] = l

        console.log("Not present: "+name+", coord: " +String(l))
        return l
      }
    }
  }
  let col =  sheet.getLastColumn()
  if( col <1){
    col = 1
  }
  let values = sheet.getRange(1, 1, 1, col).getValues()[0]
  for (i = 0; i < values.length; i++) {
    pos[values[i]] = i+1
  }

  let row = sheet.getLastRow()
  let lastDate = 0
  if (row > 1){
    lastDate = sheet.getRange(row , pos.safeGet("uploaded_at")).getValue()
  }
  str = ""
  row = Math.max(2, row + 1)
  content.forEach((match) => {
    if (Number(match["uploaded_at"]) <= lastDate) {
      return;
    }
    for (k in match) {
      col = pos.safeGet(k)
      sheet.getRange(row, col).setValue(match[k])
    }
    row++

  })}


function doPost(e) {
  fillContent(e.postData.contents)
  return ContentService.createTextOutput("ok").setMimeType(ContentService.MimeType.TEXT);
}


