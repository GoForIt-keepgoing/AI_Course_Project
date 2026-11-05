/* ================= 动态题库（分层练习用） ================= */
const BANK = {
  types: [
    { key: "choice", name: "单项选择" },
    { key: "fill", name: "选词填空" },
    { key: "dialogue", name: "补全对话" },
    { key: "reorder", name: "连词成句" }
  ],

  choice: [
    { lv: 1, q: "—What would you like to eat?\n—I'd like a ______.", options: ["hamburger", "hamburgers", "hamburger please"], answer: 0, explain: "I'd like a + 可数名词单数。" },
    { lv: 1, q: "—What would you like to ______?\n—A cup of tea.", options: ["eat", "drink", "read"], answer: 1, explain: "喝用 drink。" },
    { lv: 1, q: "I'd like ______ orange juice.", options: ["a", "an", "some"], answer: 2, explain: "juice 不可数，用 some。" },
    { lv: 2, q: "—Would you like some tea?\n—Yes, ______.", options: ["I am", "please", "thanks you"], answer: 1, explain: "礼貌接受用 Yes, please." },
    { lv: 2, q: "—What ______ you like?\n—I'd like some salad.", options: ["do", "would", "are"], answer: 1, explain: "Would you like ...? 表示委婉询问。" },
    { lv: 2, q: "—How much is it?\n—It's ______ yuan.", options: ["thirty", "thirtieth", "thirteen of"], answer: 0, explain: "价格用基数词 thirty。" },
    { lv: 3, q: "—What would you like ______?\n—A hamburger, please.", options: ["eat", "to eat", "eating"], answer: 1, explain: "would like to do sth." },
    { lv: 3, q: "I'd like two ______, please.", options: ["hamburger", "hamburgers", "a hamburger"], answer: 1, explain: "two + 可数名词复数。" },
    { lv: 3, q: "—______ would you like to drink?\n—Some juice.", options: ["What", "How", "Where"], answer: 0, explain: "询问“想喝什么”用 What。" }
  ],

  fill: [
    { lv: 1, q: "I'd like a ______ (hamburger).", answer: "hamburger", explain: "a + 单数。" },
    { lv: 1, q: "Would you like some ______ (tea)?", answer: "tea", explain: "tea 不可数。" },
    { lv: 1, q: "I'm ______ (hungry). Let's eat.", answer: "hungry", explain: "形容词作表语。" },
    { lv: 2, q: "I'd like two ______ (sandwich).", answer: "sandwiches", explain: "two + 复数。" },
    { lv: 2, q: "She ______ (like) salad.", answer: "likes", explain: "第三人称单数加 -s。" },
    { lv: 2, q: "We ______ (have) four classes.", answer: "have", explain: "we 后用原形。" },
    { lv: 3, q: "He ______ (go) to school by bus.", answer: "goes", explain: "第三人称单数 goes。" },
    { lv: 3, q: "There ______ (be) some milk in the glass.", answer: "is", explain: "milk 不可数，用 is。" },
    { lv: 3, q: "I'd like ______ (buy) a T-shirt.", answer: "to buy", explain: "would like to do。" }
  ],

  dialogue: [
    { lv: 1, q: "A: What would you like to eat?\nB: ______", options: ["I'd like a salad.", "I'm fine.", "It's sunny."], answer: 0 },
    { lv: 1, q: "A: Would you like some tea?\nB: ______", options: ["Yes, please.", "I'm ten.", "It's red."], answer: 0 },
    { lv: 1, q: "A: ______\nB: I'd like some juice.", options: ["What would you like to drink?", "What's your name?", "How old are you?"], answer: 0 },
    { lv: 2, q: "A: How much is it?\nB: ______", options: ["It's twenty yuan.", "I'm fine.", "Yes, please."], answer: 0 },
    { lv: 2, q: "A: ______\nB: Yes, I'd like a hamburger.", options: ["Can I help you?", "How are you?", "Where are you?"], answer: 0 },
    { lv: 2, q: "A: What size do you need?\nB: ______", options: ["Size M, please.", "It's blue.", "Thank you."], answer: 0 },
    { lv: 3, q: "A: ______\nB: I'm going to Beijing.", options: ["Where are you going?", "How are you?", "What's this?"], answer: 0 },
    { lv: 3, q: "A: Do you have a fever?\nB: ______", options: ["Yes, I do.", "Yes, I am.", "Yes, I can."], answer: 0 },
    { lv: 3, q: "A: ______\nB: It's sunny.", options: ["What's the weather like?", "How old are you?", "What's your name?"], answer: 0 }
  ],

  reorder: [
    { lv: 1, words: ["like", "I'd", "a", "hamburger"], answer: "I'd like a hamburger" },
    { lv: 1, words: ["would", "What", "you", "like"], answer: "What would you like" },
    { lv: 1, words: ["some", "I'd", "juice", "like"], answer: "I'd like some juice" },
    { lv: 2, words: ["to", "What", "you", "like", "drink", "would"], answer: "What would you like to drink" },
    { lv: 2, words: ["is", "How", "it", "much"], answer: "How much is it" },
    { lv: 2, words: ["a", "I", "T-shirt", "buy", "want", "to"], answer: "I want to buy a T-shirt" },
    { lv: 3, words: ["going", "I'm", "Beijing", "to"], answer: "I'm going to Beijing" },
    { lv: 3, words: ["playing", "likes", "She", "football"], answer: "She likes playing football" },
    { lv: 3, words: ["on", "We", "English", "Monday", "have"], answer: "We have English on Monday" }
  ]
};
