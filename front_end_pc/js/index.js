var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        username: sessionStorage.username || localStorage.username,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        cart_total_count: 0, // 购物车总数量
        cart: [], // 购物车数据,
        f1_tab: 1, // 1F 标签页控制
        f2_tab: 1, // 2F 标签页控制
        f3_tab: 1, // 3F 标签页控制
    },
    mounted: function(){
        this.get_cart();

        // 获取购物车数据
        axios.get(this.host+'/carts/', {
                headers: {
                    'Authorization': 'JWT ' + this.token
                },
                responseType: 'json',
                withCredentials: true
            })
            .then(response => {
                this.cart = response.data;


                for (let i = 0; i < this.cart.length ; i++) {
                    this.cart_total_count += response.data[i].count;

                    this.name = response.data[i].name;

                    if (this.name.length >= 25){
                        this.cart[i].name = this.name.substring(0, 25) + '...';
                    }

                }



            })
            .catch(error => {
                console.log(error.response.data);
            })

    },

    methods: {
        // 退出
        logout: function(){
            sessionStorage.clear();
            localStorage.clear();
            location.href = '/login.html';
        },
        // 获取购物车数据
        get_cart: function(){

        }
    }
});