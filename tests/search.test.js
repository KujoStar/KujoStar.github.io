const test = require("node:test");
const assert = require("node:assert/strict");
const {search, normalize, snippet} = require("../docs/javascripts/search-core.js");
const items = [
  {id:"avl",title:"Lab3 Report",category:"课程笔记",subcategory:"数据结构与算法",tags:["DSA解题报告"],date:"2023-01-26",text:"AVL 树维护平衡因子。树的旋转操作。"},
  {id:"notes",title:"概率论",category:"课程笔记",subcategory:"概率统计",tags:["概统"],date:"2023-01-11",text:"随机变量与统计推断。"},
  {id:"title",title:"AVL 学习笔记",category:"科研项目",subcategory:"算法",tags:[],date:"2020-01-01",text:"实验"}
];
test("Chinese body matches and title matches rank first", () => {
  assert.deepEqual(search(items,"平衡因子").map(x=>x.id),["avl"]);
  assert.deepEqual(search(items,"AVL").map(x=>x.id),["title","avl"]);
});
test("Unicode, tags, multiword matching, empty and no result", () => {
  assert.equal(normalize("  ＡＶＬ  "),"avl");
  assert.equal(search(items,"avl 平衡")[0].id,"avl");
  assert.equal(search(items,"DSA")[0].id,"avl");
  assert.deepEqual(search(items,""),[]);
  assert.deepEqual(search(items,"不存在"),[]);
  assert.deepEqual(search(items,"AVL 概统"),[]);
});
test("Snippet finds body match, and cache belongs to each immutable index object", () => {
  assert.match(snippet(items[0],"平衡"),/平衡/);
  const replacement = {...items[0],text:"新正文"};
  assert.equal(search([replacement],"新正文").length,1);
});
