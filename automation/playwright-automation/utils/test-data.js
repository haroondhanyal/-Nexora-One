import { faker } from '@faker-js/faker';

faker.seed(20261008);

export function uniqueTestValue(prefix = 'Nexora QA') {
  return `${prefix} ${faker.string.uuid()}`;
}

export function testCorrelationId(prefix = 'NX-E2E') {
  return `${prefix}-${faker.string.uuid()}`;
}

export function fakeProject() {
  return {
    name: `${faker.company.buzzNoun()} ${faker.string.alphanumeric(6)}`,
    owner: faker.person.fullName(),
    description: faker.lorem.sentence(),
  };
}

export function fakeContact() {
  return {
    name: faker.person.fullName(),
    email: faker.internet.email().toLowerCase(),
    phone: faker.phone.number(),
  };
}
