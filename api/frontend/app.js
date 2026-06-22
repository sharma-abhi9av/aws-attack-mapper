const API='';let cy,selId=null,pathSrc=null,pathTgt=null;
const TC={
  User:{color:'#5383e9',icon:'User',label:'User'},
  Role:{color:'#f0b90b',icon:'Role',label:'Role'},
  Group:{color:'#32915c',icon:'Group',label:'Group'},
  Policy:{color:'#5cad7a',icon:'Policy',label:'Policy'},
  S3Bucket:{color:'#a26ee0',icon:'S3',label:'S3 Bucket'},
  EC2Instance:{color:'#d9544d',icon:'EC2',label:'EC2'},
  SecurityGroup:{color:'#7aa7d4',icon:'SecurityGroup',label:'Security Group'},
  default:{color:'#484f58',icon:'circle',label:'Node'}
};
function tc(t){return TC[t]||TC.default}
function esc(s){if(s==null)return'';const d=document.createElement('div');d.textContent=String(s);return d.innerHTML}

document.addEventListener('DOMContentLoaded',()=>{initCy();loadStats();listen();showInitial()});

function initCy(){
  const ss=[
    {selector:'node',style:{label:'data(name)','font-size':'11px','font-weight':500,color:'#e1e4e8','font-family':'Inter,-apple-system,BlinkMacSystemFont,sans-serif','text-valign':'bottom','text-halign':'center','text-margin-y':4,width:36,height:36,shape:'rectangle','background-color':'transparent','background-fit':'contain','background-width':'100%','background-height':'100%','background-image-opacity':1,'border-width':0,'border-color':'transparent'}},
    {selector:'edge',style:{width:2,'line-color':'#30363d','target-arrow-color':'#484f58','target-arrow-shape':'triangle','curve-style':'bezier','arrow-scale':1.2,label:'data(relationship)','font-size':'7px','font-weight':600,color:'#484f58','text-rotation':'autorotate','text-background-color':'#0b0e12','text-background-opacity':.85,'text-background-padding':2}},
    {selector:'node.source',style:{'border-width':2,'border-color':'#238636'}},
    {selector:'node.target',style:{'border-width':2,'border-color':'#c12c2c'}},
    {selector:'node.hv',style:{'border-width':2,'border-color':'#c12c2c'}},
    {selector:'.path-edge',style:{'line-color':'#d29922','target-arrow-color':'#d29922',width:3,'z-index':10}},
    {selector:'.path-node',style:{'border-width':2,'border-color':'#d29922','z-index':5}},
    {selector:'edge[relationship="GRANTS_ACCESS"]',style:{'line-style':'dashed','line-color':'#58a6ff','target-arrow-color':'#58a6ff',width:1.5}},
  ];
  for(const[t,c]of Object.entries(TC))
    ss.push({selector:`node[type="${t}"]`,style:{'background-image':`url(icons/${c.icon}.svg)`}});
  ss.push({selector:'node[type="default"]',style:{width:36,height:36,shape:'rectangle','background-color':'#21262d','background-image':'none','border-width':2,'border-color':'#30363d',opacity:.5}});

  cy=cytoscape({container:document.getElementById('cy'),style:ss,minZoom:.08,maxZoom:6,wheelSensitivity:.3,selectionType:'single'});
  cy.on('tap','node',e=>{const n=e.target;selId=n.data('id');showDetail(selId).then(r=>{if(r&&!r.added)cy.animate({center:{eles:n},zoom:1.5,duration:300})})});
  cy.on('tap','_',e=>{if(e.target===cy){hideDetail();hideCtx();cy.elements().removeClass('selected highlighted');selId=null}});
  cy.on('cxttap','node',e=>{e.preventDefault();const n=e.target;selId=n.data('id');showCtx(e.originalEvent.clientX,e.originalEvent.clientY,selId)});
  cy.on('cxttap','_',e=>{if(e.target===cy)hideCtx()});
}

function loadStats(){
  fetch(API+'/api/stats').then(r=>r.json()).then(s=>{
    const total=s.users+s.roles+s.groups+s.policies+s.buckets+s.instances+s.security_groups;
    const dots={User:'#5383e9',Role:'#f0b90b',Group:'#32915c',Policy:'#5cad7a',S3:'#a26ee0',EC2:'#d9544d',SG:'#7aa7d4'};
    const etLabels={MEMBER_OF:'Member',HAS_POLICY:'Policy',HAS_INLINE_POLICY:'InlinePol',USES_SG:'Uses SG',HAS_ROLE:'Has Role',GRANTS_ACCESS:'Grants Access'};
    const sv=s.high_value_targets;
    const dd=document.getElementById('stats-drop');
    dd.innerHTML=
      '<div class="sd-hdr">Database Stats</div>'+
      '<div class="sd-row"><span class="sd-lbl">Total Nodes</span><span class="sd-val">'+total.toLocaleString()+'</span></div>'+
      '<div class="sd-row"><span class="sd-lbl">Total Edges</span><span class="sd-val">'+(s.edges||0).toLocaleString()+'</span></div>'+
      '<div class="sd-hdr">By Type</div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.User+'"></span><span class="sd-ty-lbl">User</span><span class="sd-ty-val">'+(s.users||0)+'</span></div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.Role+'"></span><span class="sd-ty-lbl">Role</span><span class="sd-ty-val">'+(s.roles||0)+'</span></div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.Group+'"></span><span class="sd-ty-lbl">Group</span><span class="sd-ty-val">'+(s.groups||0)+'</span></div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.Policy+'"></span><span class="sd-ty-lbl">Policy</span><span class="sd-ty-val">'+(s.policies||0)+'</span></div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.S3+'"></span><span class="sd-ty-lbl">S3</span><span class="sd-ty-val">'+(s.buckets||0)+'</span></div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.EC2+'"></span><span class="sd-ty-lbl">EC2</span><span class="sd-ty-val">'+(s.instances||0)+'</span></div>'+
      '<div class="sd-ty"><span class="sd-dot" style="background:'+dots.SG+'"></span><span class="sd-ty-lbl">Security Group</span><span class="sd-ty-val">'+(s.security_groups||0)+'</span></div>'+
      (s.edge_types?'<div class="sd-hdr">Relationships</div><div class="sd-rels">'+Object.entries(s.edge_types).map(([k,v]) => '<span class="sd-rel"><span class="sd-rel-val">'+v+'</span> '+(etLabels[k]||k)+'</span>').join('')+'</div>':'');
    document.querySelector('.sr-actions').classList.add('has-stats');
    const hv=s.high_value_targets,t=hv.admin_users+hv.open_security_groups+hv.public_buckets+hv.leaky_roles;
    const b=document.getElementById('btn-hv');
    if(t){b.classList.add('show');document.getElementById('hv-count').textContent=t;b.title=`${hv.admin_users} admin · ${hv.open_security_groups} open SG · ${hv.public_buckets} public bucket · ${hv.leaky_roles} leaky role`}
  });
}

async function showDetail(id){
  const panel=document.getElementById('detail');
  panel.classList.remove('hidden');
  const g=await fetch(API+'/api/graph/neighbors/'+encodeURIComponent(id)).then(r=>r.json());
  const me=g.nodes.find(n=>n.id===id);if(!me)return{added:false,id};
  const p=me.properties||{};
  const mType=(me.labels||[me.label||'default'])[0],mCfg=tc(mType);

  document.getElementById('d-title').textContent=p.name||id;
  document.getElementById('d-type').innerHTML=`<img src="icons/${mCfg.icon}.svg" class="d-type-icon"> ${mCfg.label}`;
  document.getElementById('d-type').style.color=mCfg.color;
  document.getElementById('d-arn').textContent=p.arn||id;

  let html='';
  const keys=Object.keys(p).filter(k=>k!=='document');
  if(keys.length){
    html+=`<div class="ds"><div class="ds-title">Properties</div>`;
    for(const k of keys)
      typeof p[k]!=='object'
        ?html+=`<div class="pr"><span class="pk">${esc(k)}</span><div class="pv">${esc(String(p[k]))}</div></div>`
        :html+=`<div class="pr"><span class="pk">${esc(k)}</span><div class="pv"><pre>${esc(JSON.stringify(p[k],null,2))}</pre></div></div>`;
    html+=`</div>`
  }

  // Build connections list (always show ALL)
  if(g.edges.length){
    html+=`<div class="ds"><div class="ds-title">Connections (${g.edges.length})</div><div class="el">`;
    for(const e of g.edges){
      const out=e.source===id,tid=out?e.target:e.source;
      const tn=g.nodes.find(n=>n.id===tid),tnm=tn?.properties?.name||tn?.name||tid,tType=tn?.labels?.[0]||tn?.label||'',tCfg=tc(tType);
      html+=`<div class="eli" onclick="focusNode('${esc(tid)}')"><span class="ed">${out?'→':'←'}</span><span class="er">${esc(e.relationship)}</span><span class="et"><img src="icons/${tCfg.icon}.svg" style="width:12px;height:12px;filter:brightness(0) invert(1);"> ${esc(tnm)}</span></div>`
    }
    html+=`</div></div>`
  }
  document.getElementById('d-content').innerHTML=html;

  // Limit Policy/BucketPolicy/InlinePolicy nodes in graph to 5
  let pc=0;
  const gn=g.nodes.filter(n=>{
    const t=(n.labels||[n.label||'default'])[0];
    if(t==='Policy'||t==='BucketPolicy'||t==='InlinePolicy'){pc++;return pc<=5}
    return true
  });
  const added=loadGraph({nodes:gn,edges:g.edges},id);
  if(added){
    const e=cy.getElementById(id);
    if(e.length)cy.animate({center:{eles:e},zoom:1.5,duration:300})
  }
  return{added,id}
}

function hideDetail(){document.getElementById('detail').classList.add('hidden')}
function focusNode(id){
  const el=cy.getElementById(id);
  if(el.length){cy.animate({center:{eles:el},zoom:1.5,duration:300})}
  showDetail(id)
}

function showInitial(){
  fetch(API+'/api/users').then(r=>r.json()).then(users=>{
    if(!users||!users.length)return;
    for(const u of users){
      if(!u.id)continue;
      cy.add({group:'nodes',data:{id:u.id,name:u.name||u.id,type:'User'}})
    }
    cy.layout({name:'circle',spacingFactor:2,fit:true,padding:80}).run();
    setTimeout(()=>{
      const el=cy.nodes().first();
      if(el.length)cy.animate({center:{eles:el},zoom:2,duration:300})
    },400)
  })
}

function loadGraph(d,centerId){
  if(!d||!d.nodes||!d.nodes.length)return false;
  const parentEl=centerId?cy.getElementById(centerId):null;
  const pp=parentEl?.length?parentEl.position():null;
  const newIds=[];
  for(const n of d.nodes){
    if(!n.id)continue;
    const type=(n.labels||[n.label||'default'])[0],name=n.properties?.name||n.name||n.properties?.arn?.split('/').pop()||n.arn?.split('/').pop()||n.id;
    if(!cy.getElementById(n.id).length){
      let pos;
      if(pp){
        const angle=Math.random()*2*Math.PI;
        const dist=130+Math.random()*70;
        pos={x:pp.x+Math.cos(angle)*dist,y:pp.y+Math.sin(angle)*dist}
      }
      cy.add({group:'nodes',data:{id:n.id,name,type},position:pos});
      newIds.push(n.id)
    }
  }
  let added=newIds.length>0;
  for(const e of d.edges){
    if(!e.source||!e.target)continue;
    const eid=`${e.source}-${e.target}-${e.relationship||e.type||''}`;
    if(!cy.getElementById(eid).length&&cy.getElementById(e.source).length&&cy.getElementById(e.target).length)
      cy.add({group:'edges',data:{id:eid,source:e.source,target:e.target,relationship:e.relationship||e.type||''}})
  }
  return added
}

// ─── Context Menu ─────────────────
let ctxNodeId=null;
function showCtx(x,y,id){
  hideCtx();
  ctxNodeId=id;
  const el=document.getElementById('ctx-menu');
  el.style.left=x+'px';el.style.top=y+'px';
  el.classList.remove('hidden');
  document.querySelectorAll('.ctx-item[data-act]').forEach(b=>{
    const a=b.dataset.act;
    b.classList.toggle('is-set',(a==='setsrc'?pathSrc:a==='settgt'?pathTgt:null)===id)
  })
}
function hideCtx(){const el=document.getElementById('ctx-menu');el.classList.add('hidden');ctxNodeId=null}
function ctxAction(a){
  const id=ctxNodeId;if(!id)return;hideCtx();
  if(a==='setsrc'){setSource(pathSrc===id?null:id);hideDetail()}
  else if(a==='settgt'){setTarget(pathTgt===id?null:id);hideDetail()}
    else if(a==='neighbors'){fetch(API+'/api/graph/neighbors/'+encodeURIComponent(id)).then(r=>r.json()).then(d=>loadGraph(d,id))}
    else if(a==='reachable'){fetch(API+'/api/graph/reachable/'+encodeURIComponent(id)).then(r=>r.json()).then(t=>{if(!t||!t.length)return;const g={nodes:[...t.map(n=>({id:n.id,name:n.name,labels:[n.label]}))],edges:t.map(n=>({source:id,target:n.id,relationship:'CAN_REACH'}))};if(!cy.getElementById(id).length)g.nodes.unshift({id,name:id,labels:['default']});loadGraph(g,id)})}
  else if(a==='highvalue'){const el=cy.getElementById(id);if(el.length)el.toggleClass('hv')}
  else if(a==='focus'){focusNode(id)}
  else if(a==='copy-name'){const n=cy.getElementById(id);if(n.length)navigator.clipboard.writeText(n.data('name'))}
  else if(a==='copy-id'){navigator.clipboard.writeText(id)}
}

// ─── Pathfinding ─────────────────
function setSource(id){pathSrc=id;cy.elements().removeClass('source');if(id)cy.getElementById(id).addClass('source');updatePathBar()}
function setTarget(id){pathTgt=id;cy.elements().removeClass('target');if(id)cy.getElementById(id).addClass('target');updatePathBar()}
function updatePathBar(){
  const bar=document.getElementById('path-bar');
  if(!pathSrc&&!pathTgt){bar.classList.add('hidden');return}
  bar.classList.remove('hidden');
  const s=document.getElementById('path-source'),t=document.getElementById('path-target');
  if(pathSrc){const n=cy.getElementById(pathSrc);s.innerHTML=`<span class="pb-dot" style="background:#81c995"></span> ${esc(n.data('name')||pathSrc)}`;s.className='pb-node'}
  else{s.innerHTML='<span style="color:#5f6368;">Select source</span>';s.className='pb-node pb-empty'}
  if(pathTgt){const n=cy.getElementById(pathTgt);t.innerHTML=`<span class="pb-dot" style="background:#f28b82"></span> ${esc(n.data('name')||pathTgt)}`;t.className='pb-node'}
  else{t.innerHTML='<span style="color:#5f6368;">Select target</span>';t.className='pb-node pb-empty'}
}
function findPath(){
  if(!pathSrc||!pathTgt)return;
  const btn=document.getElementById('btn-find-path');btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>'
  cy.elements().removeClass('path-node path-edge');
  fetch(API+'/api/graph/shortest-path?from='+encodeURIComponent(pathSrc)+'&to='+encodeURIComponent(pathTgt)+'&max-depth=10')
    .then(r=>r.json()).then(d=>{
      btn.disabled=false;btn.innerHTML='<i class="fas fa-route"></i> Path';
      if(!d.nodes||!d.nodes.length){showPathMsg('No path found');return}
      showPathMsg('');displayPath(d)
    }).catch(()=>{btn.disabled=false;btn.innerHTML='<i class="fas fa-route"></i> Path';showPathMsg('Error')})
}
function showPathMsg(m){const el=document.getElementById('path-msg');if(m){el.textContent=m;el.classList.remove('hidden')}else el.classList.add('hidden')}
function displayPath(d){
  for(const n of d.nodes){const type=n.label||'default',name=n.name||n.id;if(!cy.getElementById(n.id).length)cy.add({group:'nodes',data:{id:n.id,name,type}})}
  for(const e of d.edges){const eid=`${e.source}-${e.target}-${e.type||''}`;if(!cy.getElementById(eid).length&&cy.getElementById(e.source).length&&cy.getElementById(e.target).length)cy.add({group:'edges',data:{id:eid,source:e.source,target:e.target,relationship:e.type||''}})}
  for(const n of d.nodes)cy.getElementById(n.id).addClass('path-node');
  for(const e of d.edges){const eid=`${e.source}-${e.target}-${e.type||''}`;cy.getElementById(eid).addClass('path-edge')}
  const ids=d.nodes.map(n=>'#'+n.id).join(',');const eles=cy.$(ids);
  if(eles.length){const lay=cy.layout({name:'dagre',rankDir:'LR',animate:true,animationDuration:500,spacingFactor:1.5,fit:true,padding:50});lay.promise().then(()=>cy.fit(eles,50))}
  let html='<div class="ds"><div class="ds-title">Attack Path</div><div class="path-steps">';
  for(let i=0;i<d.nodes.length;i++){const n=d.nodes[i],c=tc(n.label||'default');html+=`<div class="ps-step"><span class="ps-order">${i+1}</span><img src="icons/${c.icon}.svg" style="width:12px;height:12px;filter:brightness(0) invert(1);"> ${esc(n.name||n.id)}</div>`;if(i<d.edges.length)html+=`<div class="ps-edge"><span class="ps-rel">${esc(d.edges[i].type)}</span></div>`}
  html+='</div></div>';
  if(selId&&!document.getElementById('detail').classList.contains('hidden'))document.getElementById('d-content').innerHTML+=html
}

function listen(){
  // Search
  const search=document.getElementById('search'),results=document.getElementById('search-results');let st,skipClear=false;
  function searchFocus(id){
    selId=id;
    fetch(API+'/api/graph/neighbors/'+encodeURIComponent(id)).then(r=>r.json()).then(g=>{
      loadGraph(g,id);
      showDetail(id);
      cy.elements().removeClass('selected highlighted dimmed');
      const el=cy.getElementById(id);
      if(el.length){el.addClass('selected');el.connectedEdges().addClass('highlighted')}
      // dim everything not connected to the focused node
      cy.nodes().not(el).not(el.neighborhood()).addClass('dimmed');
      cy.edges().not(el.connectedEdges()).addClass('dimmed');
    })
  }
  search.addEventListener('input',()=>{
    clearTimeout(st);const q=search.value.trim();
    if(skipClear){skipClear=false;return}
    if(q.length<2){
      results.classList.add('hidden');
      cy.elements().removeClass('dimmed');
      return
    }
    st=setTimeout(()=>{
      fetch(API+'/api/search?q='+encodeURIComponent(q)).then(r=>r.json()).then(data=>{
        results.innerHTML='';
        if(!data.length)results.innerHTML='<div class="sr" style="padding:12px;color:#5f6368;font-size:12px;">No results</div>';
        else{
          data.slice(0,25).forEach(r=>{
            const c=tc(r.type);const d=document.createElement('div');d.className='sr';
            d.innerHTML=`<img src="icons/${c.icon}.svg" style="width:14px;height:14px;filter:brightness(0) invert(1);"><span class="sn">${esc(r.name)}</span><span class="st">${r.type}</span>`;
            d.onclick=()=>{results.classList.add('hidden');skipClear=true;search.value='';searchFocus(r.id)};results.appendChild(d)})
        }
        results.classList.remove('hidden')
      })
    },250)
  });
  search.addEventListener('blur',()=>setTimeout(()=>results.classList.add('hidden'),200));
  search.addEventListener('focus',()=>{if(results.children.length)results.classList.remove('hidden')});

  document.getElementById('btn-stats').onclick=function(e){e.stopPropagation();const d=document.getElementById('stats-drop');d.classList.toggle('hidden')};
  document.addEventListener('click',function(e){const d=document.getElementById('stats-drop');if(!d.classList.contains('hidden')&&!e.target.closest('.sr-actions'))d.classList.add('hidden')});

  document.getElementById('btn-close-detail').onclick=hideDetail;

  document.getElementById('btn-relayout').onclick=()=>{
    if(!cy||!cy.nodes().length)return;
    cy.layout({name:'dagre',rankDir:'LR',animate:true,animationDuration:400,spacingFactor:1.5,fit:true,padding:60}).run()
  };

  document.getElementById('btn-find-path').addEventListener('click',findPath);
  document.getElementById('btn-clear-path').onclick=()=>{setSource(null);setTarget(null);cy.elements().removeClass('path-node path-edge');document.getElementById('path-bar').classList.add('hidden');showPathMsg('')};

  // Ingest
  document.getElementById('btn-ingest').onclick=()=>document.getElementById('file-input').click();
  document.getElementById('file-input').onchange=function(){
    const files=this.files;if(!files||!files.length)return;
    const btn=document.getElementById('btn-ingest');
    btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
    const fd=new FormData();
    for(const f of files)fd.append('files',f);
    fetch(API+'/api/upload',{method:'POST',body:fd}).then(r=>r.json()).then(d=>{
      if(d.error){btn.innerHTML='<i class="fas fa-cloud-arrow-down"></i>';btn.disabled=false;return}
      btn.innerHTML='<i class="fas fa-check"></i>';
      loadStats();showInitial()
    }).catch(e=>{btn.innerHTML='<i class="fas fa-cloud-arrow-down"></i>';btn.disabled=false});this.value=''
  };

  // HV button
  document.getElementById('btn-hv').onclick=()=>{
    fetch(API+'/api/graph/high-value').then(r=>r.json()).then(nodes=>{
      if(!nodes||!nodes.length)return;
      for(const n of nodes){const type=n.label||'default',name=n.name||n.id;if(!cy.getElementById(n.id).length)cy.add({group:'nodes',data:{id:n.id,name,type},classes:'hv'})}
      cy.layout({name:'dagre',rankDir:'LR',animate:true,animationDuration:400,spacingFactor:1.5,fit:true,padding:40}).run()
      if(nodes.length)focusNode(nodes[0].id)
    })
  };

  // Context menu clicks
  document.querySelector('#ctx-menu').addEventListener('click',e=>{
    const item=e.target.closest('.ctx-item');if(!item)return;
    ctxAction(item.dataset.act)
  });

  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){hideDetail();hideCtx();cy.elements().removeClass('selected highlighted path-node path-edge')}
    // g key reserved
  });
}
