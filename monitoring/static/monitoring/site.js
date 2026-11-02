document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll("[data-filter]");
    const cards = document.querySelectorAll("[data-service-card]");

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const filter = button.dataset.filter;
            buttons.forEach((item) => item.classList.toggle("is-active", item === button));
            cards.forEach((card) => {
                card.hidden = filter !== "all" && card.dataset.status !== filter;
            });
        });
    });

    const dateNode = document.querySelector("[data-local-date]");
    if (dateNode) {
        dateNode.textContent = new Intl.DateTimeFormat(undefined, {
            dateStyle: "full",
        }).format(new Date());
    }
});
