from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(50))
    birth_date = Column(String(50), default='1940-01-01', nullable=False)
    phone = Column(String(50))
    funds = Column(Integer, nullable=False, default=0)

    # relationships
    review = relationship('Review', back_populates='user')
    def __repr__(self):
        return f'<user(id={self.id}, login={self.login}, password={self.password}, birth_date={self.birth_date}, phone={self.phone}, funds={self.funds})>'

class Trainer(Base):
    __tablename__ = "trainer"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    gym_id = Column(Integer, ForeignKey('gym.id'))

    # relationships
    gym = relationship('Gym', back_populates='trainer')
    review = relationship('Review', back_populates='trainer')
    trainer_services = relationship('TrainerServices', back_populates='trainer')
    trainer_schedule = relationship('TrainerSchedule', back_populates='trainer')
    def __repr__(self):
        return f'<Trainer(id={self.id}, name={self.name}, gym_id={self.gym_id})>'

class Gym(Base):
    __tablename__ = "gym"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    address = Column(String(50))
    contacts = Column(String(50))

    # relationships
    services = relationship("Service", back_populates="gym")
    trainer = relationship("Trainer", back_populates="gym")
    review = relationship("Review", back_populates="gym")
    def __repr__(self):
        return f'<Gym(id={self.id}, name={self.name}, address={self.address}, contacts={self.contacts})>'

class Reservation(Base):
    __tablename__ = "reservation"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    service_id = Column(Integer, ForeignKey('service.id'))
    trainer_id = Column(Integer, ForeignKey('trainer.id'))
    date = Column(String)
    time = Column(String)

    #relationship
    trainer = relationship('Trainer')
    user = relationship('User')
    service = relationship('Service')



    def __repr__(self):
        return f'<Reservation(id={self.id}, user_id={self.user_id}, service_id={self.service_id}, traiiner_id={self.traiiner_id}, date={self.date}, time={self.time})>'

class Review(Base):
    __tablename__ = "review"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    trainer_id = Column(Integer, ForeignKey('trainer.id'))
    gym_id = Column(Integer, ForeignKey('gym.id'))
    points = Column(Integer)
    text = Column(String)

    #relationships
    gym = relationship('Gym', back_populates='review')
    trainer = relationship('Trainer', back_populates='review')
    user = relationship('User', back_populates='review')
    def __repr__(self):
        return f'<Review(id={self.id}, user_id={self.user_id}, trainer_id={self.trainer_id}, gym_id={self.gym_id}, points={self.points}, text={self.text})>'

class Service(Base):
    __tablename__ = "service"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    duration = Column(Integer, nullable=False)
    description = Column(String(50))
    price = Column(Integer, nullable=False)
    gym_id = Column(Integer, ForeignKey('gym.id'))
    max_attendees = Column(Integer, nullable=False)

    # relationships
    gym = relationship('Gym', back_populates='services')
    trainer_services = relationship('TrainerServices', back_populates='service')
    def __repr__(self):
        return f'<Service(id={self.id}, name={self.name}, duration={self.duration}, description={self.description}, price={self.price}, gym_id={self.gym_id}, max_attendees={self.max_attendees})>'

class TrainerSchedule(Base):
    __tablename__ = "trainer_schedule"

    id = Column(Integer, primary_key=True)
    trainer_id = Column(Integer, ForeignKey('trainer.id'))
    date = Column(String(50))
    start_time = Column(String(50))
    end_time = Column(String(50))
    # relationships
    trainer = relationship('Trainer', back_populates='trainer_schedule')
    def __repr__(self):
        return f'<TrainerSchedule(id={self.id}, trainer_id={self.trainer_id}, date={self.date}, time={self.time})>'

class TrainerServices(Base):
    __tablename__ = "trainer_services"

    id = Column(Integer, primary_key=True)
    trainer_id = Column(Integer, ForeignKey('trainer.id'))
    service_id = Column(Integer, ForeignKey('service.id'))
    capacity = Column(Integer)

    # relationships
    trainer = relationship('Trainer', back_populates='trainer_services')
    service = relationship('Service', back_populates='trainer_services')
    def __repr__(self):
        return f'<TrainerServices(id={self.id}, trainer_id={self.trainer_id}, service_id={self.service_id}, capacity={self.capacity})>'