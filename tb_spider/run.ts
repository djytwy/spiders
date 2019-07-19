import * as puppeteer from 'puppeteer'
const Redis = require("ioredis");
const redis = new Redis();

const writeToRedis = (url: string, content: string) => {
    redis.hset('tb_data', url, content)
    .then(() => {
        console.log(`写入成功： ${url}`)
    })
    .catch((err: any) => {
        console.log(`写入失败:${url}`)
    })
};

const writePageNum = (num: string) => {
    redis.set('tb_page_num', num)
    .then(() => {
        console.log(`当前页码： ${num}`)
    })
    .catch((err: any) => {
        console.log(`页码写入失败: ${num}`)
    })
};

const deletePageNum = () => {
    redis.del('tb_page_num')
        .then(() => {
            console.log("tb_page_num 删除成功！")
        })
        .catch((err: any) => {
            console.log(`删除失败：${err}`)
        })
};

const run = async () => {
    let browser = await puppeteer.launch({
        headless: false,
        defaultViewport: {
            height:1080,
            width:1920,
        },
        args:[
            '--proxy-server=http://127.0.0.1:8080'
        ]
    });
    let page = await browser.newPage();
    const userAgentList = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5221.400 QQBrowser/10.0.1125.400',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0'
    ];
    const ua_msg = userAgentList[Math.floor((Math.random()*userAgentList.length))];
    await page.setUserAgent(userAgentList[Math.floor((Math.random()*userAgentList.length))]);
    console.log(`当前ua：${ua_msg}`);
    await page.goto('https://login.taobao.com/member/login.jhtml');
    await page.waitFor(1000);
    await page.click('#J_Quick2Static');
    await page.waitFor(1000);
    await page.type('#TPL_username_1','账号',{delay: 150});
    await page.type('#TPL_password_1','密码',{delay: 150});
    while(true) {
        if( await page.$('#nc_1__scale_text > span > b') ) {
            break
        }
        await page.waitFor(1000)
    }
    await page.waitFor(3000);

    const key_words = ['关键词1', '关键词2', '关键词3'];
    for(let key_word of key_words) {
        await page.goto('https://www.taobao.com/?spm=a230r.1.0.0.3b40f277ET1kBS');
        await page.type('#q',key_word, {delay:200});
        await page.click('.btn-search');
        await page.waitFor(3000);
        let pageNum: any = 1;
        while(true) {
            let nowPage = await redis.get('tb_page_num');
            console.log(`获取当前页码：${nowPage} `);
            if (nowPage != "1" && nowPage && pageNum === 1) {
                nowPage = (parseInt(nowPage) + 1).toString();
                await page.waitFor(1000);
                await page.click('.J_Input');
                await page.keyboard.press('Backspace');
                await page.type('.J_Input', nowPage, {delay: 200});
                await page.waitFor(1000);
                await page.click(".J_Submit");
                await page.waitFor(8000)
            }
            const content = await page.content();
            const url = await page.url();
            const scroll_len = Math.floor(Math.random() * 10) * 200;
            await page.evaluate(`window.scrollTo(0,${scroll_len})`);
            // if (content.includes("休息会呗，坐下来喝口水")) {
            //     console.log("IP 被ban ！！！")
            //     const cookies = await page.cookies()
            //     while(true) {
            //         if (cookies !== await page.cookies()) break
            //         else await page.waitFor(1000)
            //     }
            // }
            writeToRedis(url, content);
            const next = await page.$('.item.next > a');
            if (!next) break;
            else {
                await page.click('.item.next > a');
                await page.waitFor(1000);
                pageNum = await page.$eval('li.active > span', el => el.innerHTML);
                writePageNum(pageNum);
                const sleepTime = Math.floor(Math.random() * (60 - 5 + 1) + 5) * 1000;
                console.log(`休眠：${sleepTime / 1000}秒！`);
                await page.waitFor(sleepTime)
            }
        }
        console.log(`关于：${key_word}的数据已经爬取完毕！`);
        deletePageNum()
    }
};

run();

// writePageNum('23')
