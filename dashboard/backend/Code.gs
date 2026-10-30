/**
 * Projeto BI - Google Apps Script Backend
 * Lê dados da planilha e serve o dashboard HTML
 */

// ID da planilha com os dados
var SPREADSHEET_ID = '1F_PniuVosiQnBNQPjNAVGmzn-anqIjdbBU4MhsKkYAM';

/**
 * Ponto de entrada - serve a página HTML
 */
function doGet() {
  var template = HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Projeto BI')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  
  return template;
}

/**
 * Retorna todos os dados do dashboard em um único JSON
 */
function getDashboardData() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  
  return {
    kpis: getKpis(ss),
    receitaMensal: getReceitaMensal(ss),
    assinaturasMensal: getAssinaturasMensal(ss),
    interacoes: getInteracoes(ss),
    planos: getPlanos(ss),
    pagamentosStatus: getPagamentosStatus(ss),
    metadados: getMetadados(ss)
  };
}

/**
 * KPIs resumo
 */
function getKpis(ss) {
  var sheet = ss.getSheetByName('kpis_resumo');
  if (!sheet) return {};
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return {};
  var headers = data[0];
  var row = data[1];
  var obj = {};
  for (var i = 0; i < headers.length; i++) {
    obj[headers[i]] = row[i];
  }
  return obj;
}

/**
 * Receita mensal
 */
function getReceitaMensal(ss) {
  var sheet = ss.getSheetByName('receita_mensal');
  if (!sheet) return [];
  return sheetToJson(sheet);
}

/**
 * Assinaturas mensal
 */
function getAssinaturasMensal(ss) {
  var sheet = ss.getSheetByName('assinaturas_mensal');
  if (!sheet) return [];
  return sheetToJson(sheet);
}

/**
 * Interações por tipo
 */
function getInteracoes(ss) {
  var sheet = ss.getSheetByName('interacoes_por_tipo');
  if (!sheet) return [];
  return sheetToJson(sheet);
}

/**
 * Assinaturas por plano
 */
function getPlanos(ss) {
  var sheet = ss.getSheetByName('assinaturas_por_plano');
  if (!sheet) return [];
  return sheetToJson(sheet);
}

/**
 * Pagamentos por status mensal
 */
function getPagamentosStatus(ss) {
  var sheet = ss.getSheetByName('pagamentos_status_mensal');
  if (!sheet) return [];
  return sheetToJson(sheet);
}

/**
 * Metadados
 */
function getMetadados(ss) {
  var sheet = ss.getSheetByName('metadados');
  if (!sheet) return {};
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return {};
  var headers = data[0];
  var row = data[1];
  var obj = {};
  for (var i = 0; i < headers.length; i++) {
    obj[headers[i]] = row[i];
  }
  return obj;
}

/**
 * Converte uma sheet em array de objetos JSON
 */
function sheetToJson(sheet) {
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return [];
  var headers = data[0];
  var rows = [];
  for (var i = 1; i < data.length; i++) {
    var obj = {};
    for (var j = 0; j < headers.length; j++) {
      obj[headers[j]] = data[i][j];
    }
    rows.push(obj);
  }
  return rows;
}
