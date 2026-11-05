globalThis.WorkshopCases = [
 {id:'fruit',title:'水果购物：检查一段对话',topic:'水果购物',grade:'四年级',goal:'用礼貌请求购买水果，并作简单回应',known:'apple, banana, orange, pear; I’d like some …, please. / Here you are.',words:WorkshopCore.defaults().workspace.words,context:'两人一组，进行 5 分钟购物对话。学生已学本页列出的词汇和句型。请检查下面这份预设的 AI 初稿。',lines:[
 {text:'Shop assistant: Hello! What would you like?',ok:true,why:'可作为情境导入；本案例可由教师示范并配中文或图片提示。'},
 {text:'Customer: I’d like some apple, please.',reason:'英语表达',why:'some 后的可数名词通常使用复数。这里表示买一些苹果，应为 some apples。',fix:'Customer: I’d like some apples, please.'},
 {text:'Shop assistant: I would be delighted to fulfil your purchasing requirements.',reason:'难度与支架',why:'表达远超本案例设定的已有基础，也不利于学生进行简单购物交流。',fix:'Shop assistant: Here you are.'},
 {text:'Customer: Give me pears. Now!',reason:'情境与目标',why:'本案例练习礼貌请求，这种命令式表达不符合活动目标。',fix:'Customer: I’d like some pears, please.'},
 {text:'Shop assistant: Here you are. Customer: Thank you.',ok:true,why:'回应和致谢适合此处的购物交流。'}],draft:'Customer: I’d like some apples, please.\nShop assistant: Here you are.\nCustomer: Thank you.',hint:'看看 some 后的名词，再想想对话难度和礼貌表达。'},
 {id:'animal',title:'动物主题：活动难度合适吗',topic:'动物猜谜',grade:'三年级',goal:'根据外形或动作线索猜动物，并说一句简单描述',known:'cat, dog, bird, fish; It is … / It can …',words:[{word:'cat',meaning:'猫',clues:['It has four legs.','It can run.','It says meow.']},{word:'dog',meaning:'狗',clues:['It has four legs.','It can run.','It says woof.']},{word:'bird',meaning:'鸟',clues:['It has two legs.','It can fly.','It has wings.']},{word:'fish',meaning:'鱼',clues:['It lives in water.','It can swim.','It has no legs.']}],context:'学生已学四个动物词和两个简单句型，尚未学习复杂科学词汇。目标是简单口语描述。',lines:[
 {text:'先展示四种动物图片，带学生回顾名称。',ok:true,why:'激活已有知识，为后面的描述做准备。'},
 {text:'直接让学生阅读：This nocturnal mammal exhibits sophisticated echolocation.',reason:'难度与支架',why:'科学词汇和句型超出本案例基础，需要换成已学表达或增加明确支架。',fix:'出示动物图片，用 It is … / It can … 作简短示范。'},
 {text:'请每名学生立即独立写一篇 150 词英文说明文。',reason:'情境与目标',why:'长篇写作与本次简单口语描述目标不一致，也缺少语言准备。',fix:'两人合作：一人用两条简单线索描述，另一人猜测。'},
 {text:'猜不出的学生离开游戏，不再参与。',reason:'课堂实施',why:'淘汰会减少需要支架的学生的练习机会，可改为提供图片和句型后再次尝试。',fix:'猜不出时可查看图片或句型卡，与同伴讨论后再次回答。'}],draft:'One student: It has four legs. It says meow.\nPartner: A cat!\n提供动物图片及 It is … / It can … 句型卡。',hint:'检查陌生语言、学习目标和参与机会。'},
 {id:'school',title:'校园生活：这份教案能落地吗',topic:'校园生活',grade:'四年级',goal:'用简单句型询问地点，并给出回答',known:'classroom, library, playground, music room; Where is …? / It is …',words:[{word:'classroom',meaning:'教室',clues:['We learn here.','We have desks here.','We have lessons here.']},{word:'library',meaning:'图书馆',clues:['There are many books here.','We read here.','We keep quiet here.']},{word:'playground',meaning:'操场',clues:['We play here.','We can run here.','It is outside.']},{word:'music room',meaning:'音乐教室',clues:['We sing here.','We learn music here.','We can play the piano here.']}],context:'40 人班级，活动仅有 8 分钟。教室只有一台教师电脑和投影，不要求学生使用手机。',lines:[
 {text:'用校园简图复习四个地点名称，用时 1 分钟。',ok:true,why:'可以投影示范，时间与活动准备相符。'},
 {text:'全班 40 名学生每人上台对话 1 分钟，计划用时 4 分钟。',reason:'课堂实施',why:'即使不计换人时间，逐人展示也需要至少40分钟，超出8分钟活动条件。',fix:'两人并行练习 4 分钟，再邀请两组展示。'},
 {text:'每名学生用自己的手机注册 AI 账号并实时问路。',reason:'设备与条件',why:'案例明确不要求学生使用手机；活动应使用投影和纸质地图，由教师组织。',fix:'教师投影校园地图，学生用纸质角色卡两人练习。'},
 {text:'只凭游戏完成速度，判断每名学生已经掌握了问路句型。',reason:'学习检查',why:'完成快慢不能独立证明句型掌握。需要听取目标表达或让学生完成简短迁移任务。',fix:'活动结束前抽取两组对话，并让每人完成一次询问和回应。'}],draft:'A: Where is the library?\nB: It is next to the classroom.\n先用简图解释 next to，再两人练习；教师巡听并记录需要支架的表达。',hint:'关注人数与时间、设备，以及真正能反映学习的证据。'}
];
