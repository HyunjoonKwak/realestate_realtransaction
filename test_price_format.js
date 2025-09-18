function formatPrice(amount) {
    if (amount >= 10000) {
        const eok = Math.floor(amount / 10000);
        const man = amount % 10000;
        if (man === 0) {
            return `${eok.toLocaleString()}억원`;
        } else {
            return `${eok.toLocaleString()}억 ${man.toLocaleString()}만원`;
        }
    } else {
        return `${amount.toLocaleString()}만원`;
    }
}

// 테스트 데이터
const testPrices = [7350, 18300, 23000, 29800, 14400, 13000, 59700, 62300];

testPrices.forEach(price => {
    console.log(`${price} -> ${formatPrice(price)}`);
});
