const localtunnel = require('localtunnel');
(async () => {
    try {
        const tunnel = await localtunnel({ port: 3000 }); // The container maps 3001 to 3000, but local requests to localhost:3001 usually go to the host. 
        // Wait, the Next.js server is in docker compose maps host 3001 -> container 3000. So from the host machine where I am running this script, it is port 3001.
        console.log("Tunnel URL: ", tunnel.url);
        tunnel.on('close', () => {
            console.log("Tunnel closed");
        });
        tunnel.on('error', (err) => {
            console.error("Tunnel error:", err);
        });
    } catch (err) {
        console.error("Fatal error starting tunnel:", err);
    }
})();
