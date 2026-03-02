const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
    const files = await prisma.file.findMany({
        orderBy: { createdAt: 'desc' },
        take: 5
    });
    console.log("Latest Files in DB:");
    console.log(JSON.stringify(files, null, 2));
}

main()
    .catch(e => { console.error(e); process.exit(1); })
    .finally(async () => { await prisma.$disconnect(); });
