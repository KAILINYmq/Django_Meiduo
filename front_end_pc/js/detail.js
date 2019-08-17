var vm = new Vue({
    el: '#app',
    // 修改Vue变量语法，避免和Django模板冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        username: sessionStorage.username || localStorage.username,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        tab_content: {
            detail: true,
            pack: false,
            comment: false,
            service: false
        },
        sku_id: '',
        sku_count: 1,
        sku_price: price,
        cart_total_count: 0, // 购物车总数量
        cart: [], // 购物车数据
        count: 0,
        goods_stock:1,  // 库存
        hots: [], // 热销商品
        cat: cat, // 商品类别
        comments: [], // 评论信息
        score_classes: {
            1: 'stars_one',
            2: 'stars_two',
            3: 'stars_three',
            4: 'stars_four',
            5: 'stars_five',
        }
    },
    computed: {
        sku_amount: function () {
            return (this.sku_price * this.sku_count).toFixed(2);
        }
    },
    mounted: function () {
        // 添加用户浏览历史记录
        this.get_sku_id();

        if (this.user_id) {
            axios.post(this.host + '/browse_histories/', {
                sku_id: this.sku_id
            }, {
                headers: {
                    'Authorization': 'JWT ' + this.token
                }
            })
        }

        // 判断库存数量
        axios.get(this.host + '/GoodsInventory/'　+ this.sku_id + '/', {

            // jwt　携带之后　必须通过认证才可以查询，，如果用户没有登陆则不能查询出数据
            // headers: {
            //     'Authorization': 'JWT ' + this.token
            // },
            responseType: 'json',
            withCredentials: true
        })
            .then(response => {
                this.goods_stock = response.data.goods_stock;

            })
            .catch(error => {
                console.log(error.response.data);
            });


        // 获取购物车数据
        axios.get(this.host + '/carts/', {
            headers: {
                'Authorization': 'JWT ' + this.token
            },
            responseType: 'json',
            withCredentials: true
        })
            .then(response => {
                this.cart = response.data;


                for (let i = 0; i < this.cart.length; i++) {
                    this.cart_total_count += response.data[i].count;

                    this.count = response.data[i].count;

                    this.name = response.data[i].name;

                    if (this.name.length >= 25) {
                        this.cart[i].name = this.name.substring(0, 25) + '...';
                    }

                }


            })
            .catch(error => {
                console.log(error.response.data);
            })


        // this.get_cart();
        // this.get_hot_goods();
        // this.get_comments();
    },
    methods: {
        // 退出
        logout: function () {
            sessionStorage.clear();
            localStorage.clear();
            location.href = '/login.html';
        },
        // 控制页面标签页展示
        on_tab_content: function (name) {
            this.tab_content = {
                detail: false,
                pack: false,
                comment: false,
                service: false
            };
            this.tab_content[name] = true;
        },
        // 从路径中提取sku_id
        get_sku_id: function () {
            var re = /^\/goods\/(\d+).html$/;
            this.sku_id = document.location.pathname.match(re)[1];
        },

        // 输入的商品数量失去焦点事件
        countblue:function(){
            if (this.sku_count > this.goods_stock){
                this.sku_count = this.goods_stock;
            }
            if(this.sku_count < 1){
                this.sku_count = 1;
            }
        },

        // 增加最大值
        on_maxs:function(){
            this.sku_count++;
            if (this.sku_count > this.goods_stock){
                this.sku_count = this.goods_stock;
            }
        },

        // 减小数值
        on_minus: function () {
            if (this.sku_count > 1) {
                this.sku_count--;
            }
        },
        // 添加购物车
        add_cart: function () {
            axios.post(this.host + '/carts/', {
                sku_id: parseInt(this.sku_id),
                count: this.sku_count
            }, {
                headers: {
                    'Authorization': 'JWT ' + this.token
                },
                responseType: 'json',
                withCredentials: true  // 跨域时可以携带cookie
            })
                .then(response => {
                    // alert('添加购物车成功');
                    this.cart_total_count += response.data.count;


                    // 获取购物车数据
                    axios.get(this.host + '/carts/', {
                        headers: {
                            'Authorization': 'JWT ' + this.token
                        },
                        responseType: 'json',
                        withCredentials: true
                    })
                        .then(response => {
                            this.cart = response.data;


                            for (let i = 0; i < this.cart.length; i++) {

                                this.count = response.data[i].count;

                                this.name = response.data[i].name;

                                if (this.name.length >= 25) {
                                    this.cart[i].name = this.name.substring(0, 25) + '...';
                                }

                            }


                        })
                        .catch(error => {
                            console.log(error.response.data);
                        })


                })
                .catch(error => {
                    if ('non_field_errors' in error.response.data) {
                        alert(error.response.data.non_field_errors[0]);
                    } else {
                        alert('添加购物车失败');
                    }
                    console.log(error.response.data);
                })
        },
        // 获取购物车数据
        get_cart: function () {

        },
        // 获取热销商品数据
        get_hot_goods: function () {

        },
        // 获取商品评价信息
        get_comments: function () {

        }
    }
});
