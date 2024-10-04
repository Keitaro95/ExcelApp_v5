document.addEventListener('DOMContentLoaded', function() {
    const tabLinks = document.querySelectorAll('.tab-menu a');
    const tabContents = document.querySelectorAll('.tab-content');
  
    tabLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
  
        // すべてのタブリンクからactiveクラスを削除
        tabLinks.forEach(l => l.classList.remove('active'));
        // クリックされたタブリンクにactiveクラスを追加
        this.classList.add('active');
  
        // すべてのタブコンテンツからactiveクラスを削除
        tabContents.forEach(content => content.classList.remove('active'));
        // クリックされたタブに対応するコンテンツにactiveクラスを追加
        const targetTab = document.querySelector(this.getAttribute('href'));
        targetTab.classList.add('active');
      });
    });
  });