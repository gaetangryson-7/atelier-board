const WebSocket = require('ws');
const a = new WebSocket('ws://localhost:3000/ws'), b = new WebSocket('ws://localhost:3000/ws');
let got = [];
a.on('message', d => { const m = JSON.parse(d); if (m.type==='state' && !m.seeded) a.send(JSON.stringify({type:'seed',stickies:[{id:'t1',x:1,y:1,w:200,h:100,color:'blue',text:'seed'}]})); });
b.on('message', d => { const m = JSON.parse(d); got.push(m.type + (m.s?':'+m.s.text:'')); });
setTimeout(()=>a.send(JSON.stringify({type:'upsert',s:{id:'t1',x:5,y:5,w:200,h:100,color:'pink',text:'modifié par A'}})),800);
setTimeout(()=>{console.log(got.join(' | ')); process.exit(0)},1500);
