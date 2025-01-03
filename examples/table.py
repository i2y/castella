from pydantic import BaseModel, Field
from castella import App, DataTable, TableModel
from castella.frame import Frame


class Person(BaseModel):
    name: str = Field(..., title="Name")
    age: int = Field(..., title="Age")
    country: str = Field(..., title="Country")


persons = [
    Person(name="Alice", age=25, country="USA"),
    Person(name="Bob", age=30, country="UK"),
    Person(name="Charlie", age=35, country="Japan"),
    Person(name="David", age=40, country="China"),
    Person(name="Eve", age=45, country="Russia"),
    Person(name="Frank", age=50, country="India"),
    Person(name="Grace", age=55, country="Brazil"),
    Person(name="Helen", age=60, country="France"),
    Person(name="Ivy", age=65, country="Germany"),
    Person(name="Jack", age=70, country="Italy"),
    Person(name="Kelly", age=75, country="Canada"),
    Person(name="Larry", age=80, country="Australia"),
    Person(name="Mary", age=85, country="Spain"),
    Person(name="Nancy", age=90, country="Mexico"),
    Person(name="Olivia", age=95, country="Argentina"),
    Person(name="Peter", age=100, country="Chile"),
    Person(name="Queen", age=105, country="Peru"),
    Person(name="Roger", age=110, country="Cuba"),
    Person(name="Sally", age=115, country="Egypt"),
    Person(name="Tom", age=120, country="Greece"),
    Person(name="Ursula", age=125, country="Turkey"),
    Person(name="Victor", age=130, country="India"),
    Person(name="Wendy", age=135, country="Brazil"),
    Person(name="Xavier", age=140, country="France"),
    Person(name="Yvonne", age=145, country="Germany"),
    Person(name="Zack", age=150, country="Italy"),
    Person(name="Alpha", age=155, country="Canada"),
    Person(name="Beta", age=160, country="Australia"),
    Person(name="Gamma", age=165, country="Spain"),
    Person(name="Delta", age=170, country="Mexico"),
    Person(name="Epsilon", age=175, country="Argentina"),
    Person(name="Zeta", age=180, country="Chile"),
    Person(name="Eta", age=185, country="Peru"),
    Person(name="Theta", age=190, country="Cuba"),
    Person(name="Iota", age=195, country="Egypt"),
    Person(name="Kappa", age=200, country="Greece"),
    Person(name="Lambda", age=205, country="Turkey"),
    Person(name="Mu", age=210, country="India"),
    Person(name="Nu", age=215, country="Brazil"),
    Person(name="Xi", age=220, country="France"),
    Person(name="Omicron", age=225, country="Germany"),
    Person(name="Pi", age=230, country="Italy"),
    Person(name="Rho", age=235, country="Canada"),
    Person(name="Sigma", age=240, country="Australia"),
    Person(name="Tau", age=245, country="Spain"),
    Person(name="Upsilon", age=250, country="Mexico"),
    Person(name="Phi", age=255, country="Argentina"),
    Person(name="Chi", age=260, country="Chile"),
    Person(name="Psi", age=265, country="Peru"),
    Person(name="Omega", age=270, country="Cuba"),
    Person(name="A", age=275, country="Egypt"),
    Person(name="B", age=280, country="Greece"),
    Person(name="C", age=285, country="Turkey"),
    Person(name="D", age=290, country="India"),
    Person(name="E", age=295, country="Brazil"),
    Person(name="F", age=300, country="France"),
    Person(name="G", age=305, country="Germany"),
    Person(name="H", age=310, country="Italy"),
    Person(name="I", age=315, country="Canada"),
    Person(name="J", age=320, country="Australia"),
    Person(name="K", age=325, country="Spain"),
    Person(name="L", age=330, country="Mexico"),
    Person(name="M", age=335, country="Argentina"),
    Person(name="N", age=340, country="Chile"),
    Person(name="O", age=345, country="Peru"),
    Person(name="P", age=350, country="Cuba"),
    Person(name="Q", age=355, country="Egypt"),
    Person(name="R", age=360, country="Greece"),
    Person(name="S", age=365, country="Turkey"),
    Person(name="T", age=370, country="India"),
    Person(name="U", age=375, country="Brazil"),
    Person(name="V", age=380, country="France"),
    Person(name="W", age=385, country="Germany"),
    Person(name="X", age=390, country="Italy"),
    Person(name="Y", age=395, country="Canada"),
    Person(name="Z", age=400, country="Australia"),
]


model = TableModel.from_pydantic_model(persons)
table = DataTable(model)


# モデルを更新するスレッドを作成
def update_model():
    import time

    while True:
        time.sleep(5)
        for p in persons:
            p.age += 1
        model.reflect_pydantic_model(persons)


import threading

threading.Thread(target=update_model, daemon=True).start()


App(
    Frame("Table"),
    table,
).run()
