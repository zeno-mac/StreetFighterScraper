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
  col = Math.max(1,col)
  let values = sheet.getRange(1, 1, 1, col).getValues()[0]
  for (i = 0; i < values.length; i++) {
    pos[values[i]] = i+1
  }

  let row = sheet.getLastRow()
  let keys = []
  console.log(row)
  if (row > 1){
    keys = sheet.getRange(2,1,row, col).getValues()
  }
  str = ""
  let existingIds = new Set()
  row = Math.max(2, row + 1)
  for (i=0; i<keys.length; i++){
    //console.log(keys[i][0])
    existingIds.add(keys[i][0])
  }
  content.forEach((match) => {
    if (existingIds.has(match["id"])) {
      return;
    }
    for (k in match) {
      col = pos.safeGet(k)
      sheet.getRange(row, col).setValue(match[k])
      existingIds.add(match["id"])
    }
    row++

  })}


function doPost(e) {
  fillContent(e.postData.contents)
  return ContentService.createTextOutput("ok").setMimeType(ContentService.MimeType.TEXT);
}


