const CSGOGSI = require("node-csgo-gsi");
const udp = require("dgram");

let gsi = new CSGOGSI({
    port: 3000,
    authToken: ["Q79v5tcxVQ8u", "Team2Token", "Team2SubToken"]
});

const client = udp.createSocket("udp4");

client.send(
    Buffer.from("all"),
    5005,
    "192.168.1.126",
    err => {if (err) console.log(err)}
)

const flash_colour = [255, 255, 255];

gsi.on("player", (player) => {
    const flashed = player["state"]["flashed"] / 255;
    if (flashed > 0) {
        client.send(
            Buffer.from(flash_colour.map(x => x * flashed).join("|")),
            5005,
            "192.168.1.126",
            err => {if (err) console.log(err)}
        )
    }
});
