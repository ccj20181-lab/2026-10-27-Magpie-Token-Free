/** 财叔动效样式 v1，源于用户认可的 WorkBuddy 成片 v06（2026-10-23）。 */
export const STYLE_ID = 'caishu-editorial-v1';
export const color = Object.freeze({
  ink:'#153548', teal:'#087E78', gold:'#AE8137', red:'#B44C48',
  paper:'#FCFDFB', muted:'#6D7F89', line:'#D8E2E4', light:'#F0F4F3',
  mint:'#E5F2ED', warm:'#F8F0DF',
});
export const fontFamily = '"Avenir Next", "PingFang SC", sans-serif';
export const type = Object.freeze({title:46, body:38, label:31, table:36,
  detail:30, note:27, hero:100, weight:600, titleWeight:700, tracking:-.5});
export const stage = Object.freeze({left:28, top:470, width:1024, height:1100,
  inset:56, titleBaseline:112, footerRule:1014, footerBaseline:1060});
export const material = Object.freeze({
  shadow:'0 18px 36px rgba(15,40,53,.09)', paperShade:'#F4F7F4',
  metal:['#F4E8C3','#CBA761','#E9D6A3','#AC8139'] as const,
});
