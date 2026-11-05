/* Animals 课堂专用题库，复用完整版的五种游戏和 Lily。 */
window.ANIMALS = (() => {
  const active = new URLSearchParams(location.search).get("lesson") === "animals";
  document.documentElement.classList.toggle("animals-classroom", active);
  const words = [
    { en: "cat", cn: "猫", emoji: "🐱" },
    { en: "dog", cn: "狗", emoji: "🐶" },
    { en: "panda", cn: "熊猫", emoji: "🐼" },
    { en: "frog", cn: "青蛙", emoji: "🐸" }
  ];
  return {
    active,
    words,
    games: {
      pairs: words,
      memory: words,
      sentences: [
        { target: "What's this?", hint: "问一问：这是什么？" },
        ...words.map(({ en, cn }) => ({ target: `It's a ${en}.`, hint: `用一句话说：这是一只${cn}。` }))
      ],
      whack: { targets: words, pool: words.map(({ en }) => en) }
    },
    scene: {
      icon: "🐾", title: "Lily · Animal Park", cn: "动物园问答",
      grad: "linear-gradient(155deg,#1e6956,#133c37)",
      steps: words.map(({ en, emoji }) => ({
        dh: "What's this?", cn: "这是什么？", image: emoji,
        hint: "It's a ____.", answer: `it's a ${en}`,
        good: `Yes! It's a ${en}.`, retry: `Try: It's a ${en}.`
      }))
    }
  };
})();
